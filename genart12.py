# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageColor
import random
import math

OUT = 'genart12.png'
IMGBG = (26,21,100)  # HSV
SIZE = (1400, 900)
RINGTHICKNESS = 5
RINGCOLOR = (380, 90, 20)
RINGCOLORRANGE = (20,98)
RINGEXTRADIUS = 100
RINGCENTERSHIFT = 0  # ability to shift the centers matching


Quadrants = {1: (0, 90), 2: (90, 180), 3: (180, 270), 4: (270, 360)}
Center = (SIZE[0]//2, SIZE[1]//2)

# Calculation of RingIntRadius (internal radius of the complex ring
# consisting of 2 concentrated circles):
#    +
#    |`.EXT   EXT=INT*sqrt(2); INT=EXT/sqrt(2)
# INT|  `.
#    +----`+
#      INT
RingIntRadius = round(RINGEXTRADIUS/math.sqrt(2)) + RINGCENTERSHIFT

def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def matrix(cols, rows, init=None):
  return [[init for col in range(cols)] for x in range(rows)]

def seq(xs, *, t=None, **mod):
  'Converts `xs` to list/tuple, modifies items with args like _0=value/lambda'
  l = list(xs)
  for k in mod:
    try:
      assert k.startswith('_')
      i = int(k[1:])
      v = mod[k]
      l[i] = v(l[i]) if callable(v) else v
    except:
      continue
  if t is None:
    return tuple(l) if isinstance(xs, tuple) else list(l)
  else:
    return t(l)

# def norm_angle(ang):
#   'Normilizes angle (in usual trigonometric coordinates)'
#   ang0 = ang % 360 if ang >= 360 else ang
#   return 360 + ang0 if ang0 < 0 else ang0

def distance(pt1, pt2):
  return math.sqrt(((pt2[0] - pt1[0])**2) + ((pt2[1] - pt1[1])**2))

def polar_to_cartesian(pp, orig=None):
  '''Converts polar coordinates (angle, radius) to abstract Descartes (x,y)
  if `orig` is None or to real/global Descrates if `orig` points out the
  real cartesian coordinates of the origin point of the polar turning.
  '''
  #         |
  #   x,y---o
  #         |^  ang
  #  orig...|.\.___    Polar coord  (ang,dist) - vector tip is "x"
  #         | /:
  #         |/_:_____
  #       0,0  :
  #          orig
  ang, rad = pp
  ang = math.radians(ang)
  x = rad * math.cos(ang)
  y = rad * math.sin(ang)
  ox, oy = (0,0) if orig is None else orig
  # if to return int-s I hit strange error with multiple points very close
  # to each others, like additive error:
  return (x + ox, y + oy)

def cartesian_to_polar(p, orig=None):
  '''Cartesian (Descartes) coordinates to polar. `p` is (x,y).
  '''
  #         |
  #   x,y---o
  #         |^  ang
  #  orig...|.\.___    Polar coord  (ang,dist) - vector tip is "x"
  #         | /:
  #         |/_:_____
  #       0,0  :
  #          orig
  if orig is not None:
    length = distance(p, orig)
    x1, y1 = p[0] - orig[0], p[1] - orig[1]  # TODO is it right?
    mul = x1 * 1 - y1 * 0  # 1,0 - coords of new vector
    cos_ang = mul / (length * 1)
    ang = math.degrees(math.acos(cos_ang))
    return (length, ang)
  else:
    orig = (0, 0)
    hipot = distance(p, orig)
    sin_ang = p[1] / hipot
    ang = math.degrees(math.asin(sin_ang))
    return (hipot, ang)

def canvas_to_cartesian(pt):
  return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def cartesian_to_canvas(pt):
  return (pt[0] + (SIZE[0]/2), (SIZE[1]/2) - pt[1])

def affine(p, mx):
  x,y = p
  ((a,b,c), (d,e,f)) = mx
  x1 = a*x + b*y + c
  y1 = d*x + e*y + f
  return (x1, y1)

def circle_point(cp, radius, *, x=None, y=None):
  '''Returns 2 x-s or 2 y-s from y or x of the circle with a center `cp`:
  Returned x-s (or y-s) are naturally sorted.
  '''
  #  (x-cx)^2 + (y-cy)^2 = R^2
  #  (y-cy) = +/-sqrt(R^2 - (x-cx)^2) => y = cy +/- sqrt(R^2 - (x-cx)^2)
  #  (x-cx) = +/-sqrt(R^2 - (y-cy)^2) => x = cx +/- sqrt(R^2 - (y-cy)^2)
  cx, cy = cp
  if x is not None:
    x_cx = x - cx
    y0 = math.sqrt((radius**2) - (x_cx**2))
    return sorted((cy + y0, cy - y0))
  elif y is not None:
    y_cy = y - cy
    x0 = math.sqrt((radius**2) - (y_cy**2))
    return sorted((cx + x0, cx - x0))
  else:
    raise ValueError('Either x or y keyword arg must be passed')

def determine_line(p1, p2):
  'Determines the equation on 2 points'
  x1,y1 = p1; x2,y2 = p2
  if x1 != x2:
    k = (y1 - y2) / (x1 - x2)
    b = y2 - (k*x2)
    return dict(k=k, b=b, domain=(x1,x2), codomain=(y1,y2))
  else:
    return dict(k=math.inf, b=None, domain=(x1,x2), codomain=(y1,y2))

def draw_circle(dr, p, radius, **kw):
  l = p[0] - radius
  r = p[0] + radius
  t = p[1] - radius
  b = p[1] + radius
  dr.ellipse((l,t,r,b), **kw)

def draw_arc(dr, pt, radius, ang0, ang1, *, draw_point):
  '''`pt` - abstract cartesian coords, start/stop angels are in degrees.
  `randomization` is a dict {'every':_, 'set_point': _}.
  '''
  if ang1 < ang0:
    ang1 += 360 * (1 + (ang0 // 360)) # add N full turn like they are in ang0
  # Now make ang1 to follow ang0 (clockwise turn!), so: 120..0 is 120,121..360:
  delta_ang = abs(ang1 - ang0)
  ang1 = ang0 + delta_ang
  # arc_len = (PI * r * angle)/180
  # angle = (arc_len * 180) / (PI * r)
  # So, angle for arc_len=0.25 pixels (0.25 looks smooth):
  ang_step = (0.25 * 180) / (math.pi * max(1, radius))
  ang_step = ang_step if ang1 > ang0 else -ang_step
  ang = ang0
  while ang <= ang1:
    p = polar_to_cartesian((ang, radius), orig=pt)
    pc = cartesian_to_canvas(p)
    draw_point(dr, pc, ang)
    #draw_circle(dr, pc, width, fill=color, width=1) # "point" drawing the arc
    # dr.point(pc, fill=color)
    ang += ang_step

def to_scale(from_scale, to_scale, from_value):
  'Maps from_value from a scale from_scale to new scale/scale: to_scale'
  from_segs = from_scale[1] - from_scale[0]
  to_segs = to_scale[1] - to_scale[0]
  from_seg = from_value - from_scale[0]
  to_seg = (to_segs * from_seg) / from_segs
  to_value = round(to_scale[0] + to_seg)
  return to_value

def draw_ring_point(rotate=False):
  '`Rotate` means to shift/rotate distribution of thick/think sectors to 45 deg'
  rotate = int(rotate)
  def draw(dr, p, ang):
    ang_step = 45
    ang_from = lambda a: (a, a + ang_step)
    width_scales = [(RINGTHICKNESS, 1), (1, RINGTHICKNESS)]
    ang_seg = math.floor(ang/ang_step)
    to_scale_i = (ang_seg + rotate) % 2
    angle_scale = ang_from(ang_step*(ang//ang_step))
    width_scale = width_scales[to_scale_i]
    width = to_scale(angle_scale, width_scale, ang)
    width = max(1, width)
    cgr_up = sorted(RINGCOLORRANGE) # color gradient range
    cgr_down = sorted(RINGCOLORRANGE, reverse=True)  # the same but reversed
    vcolor_scales = [cgr_up, cgr_down]
    vcolor_scale = vcolor_scales[to_scale_i]
    vcolor = to_scale(angle_scale, vcolor_scale, ang)
    hsv = seq(RINGCOLOR, t=tuple, _2=vcolor)
    color = 'hsv(%d,%d%%,%d%%)' % hsv
    if width == 1:
      dr.point(p, fill=color)
    else:
      draw_circle(dr, p, width/2, fill=color)
  return draw

def draw_rings(dr, pins):
  pins = flat_2x2(pins)
  for p in pins:
    if p is not None:
      draw_arc(dr, p, RINGEXTRADIUS, 0, 360, draw_point=draw_ring_point())
      draw_arc(dr, p, RingIntRadius, 0, 360, draw_point=draw_ring_point(True))

def find_pins():
  '''Returns matrix of pins as Discartes coords and matrix is:
  p, p, p...  <-- row
  p, p, p...  <-- row
  I.e., result[row][col] or result[y][x]
  '''
  #      0  1  2  3  4
  # 0       +     +
  # 1    +     +     +
  # 2       +     +
  # 3    +     X     +  <-- center: (h_mid, v_mid)
  # 4       +     +
  # 5    +     +     +
  dist = RingIntRadius
  h_num = math.ceil(SIZE[0] / dist) + 1 +1 # additional +1 for "tails"
  v_num = math.ceil(SIZE[1] / dist) + 1 +1 # additional +1 for "tails"
  res = matrix(v_num, h_num, init=None)
  h_mid = h_num//2  # column of X-cross
  v_mid = v_num//2  # row of X-cross
  # giagonals can be:
  #  1. col,row are on even,even/odd,odd
  #  2. col,row are on even,odd/odd,even
  # So this phase/antiphase is encoded with `^` operation's truth-table:
  #  a b ^   which allows us to compare result of `^` over odd/even flag
  #  -----   of every cell and if it the same as `on_diag` then we are
  #  1 1 0   on the same diagonal, so we should set the point here.
  #  0 0 0   Else keep the cell as is (they all are initialized by `None`).
  #  1 0 1
  #  0 1 1
  on_diag = (h_mid%2) ^ (v_mid%2)
  # constraint values like x_0, y_0 are calculated from the middle "X"
  y_0 = v_mid * dist
  for y in range(v_num):
    x_0 = -(h_mid * dist)
    for x in range(h_num):
      if ((x%2) ^ (y%2)) == on_diag:
        res[x][y] = (x_0, y_0)
      x_0 += dist
    y_0 -= dist
  return res

def flat_2x2(mx): return [col for row in mx for col in row]

# def debug(dr, ps, color='white'):
#   for p in ps:
#     if p is not None:
#       cp = cartesian_to_canvas(p)
#       dr.point(cp, fill='red')

############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
pins_2x2 = find_pins()
#debug(dr, flat_2x2(pins_2x2))
draw_rings(dr, pins_2x2)
# draw_arc(dr, canvas_to_cartesian(Center), 200, 0, 360, draw_point=draw_ring_point())
# draw_arc(dr, canvas_to_cartesian(Center), 100, 0, 360, draw_point=draw_ring_point(True))

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')