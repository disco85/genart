# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageColor
import random
import math

OUT = 'genart11.png'
IMGBG = (26,21,84)  # HSV
SIZE = (1400, 800)
STRIPES = 5 #5 #10
STRIPEWIDTH = 20 #10 #20
RINGCOLOR = (26,21,84)  # HSV (light, spaces)
STRIPECOLOR = (184,34,20)  # HSV (dark, stripes)
ROUGHNESSFIX = 0 #-2  if circle stripes dont match each others perfectly


assert 1 < STRIPES, 'Invalid STRIPES value'

Quadrants = {1: (0, 90), 2: (90, 180), 3: (180, 270), 4: (270, 360)}
RingRadius = STRIPEWIDTH * 2 * STRIPES

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

def stripes_distribution():
  '''Returns stripes distribution as a list dicts:
  {'stripe_beg': _, 'stripe_end': _, 'space_beg': _, 'space_end': _} inside
  bigger dict {'distr': _, 'pins_dist': _} where `distr` is the distribution,
  `pins_dist` is distance b/w pins.
  '''
  toint = math.ceil
  def intdict(d):
    for k, v in d.items():
      try: d[k] = toint(v)
      except: pass
    return d
  #  If w: width of a stripe/space then:
  #  whole = STRIPES*w + (STRIPES-1)*w + gap
  #
  #  <------ RingRadius ------>
  #  |  4 |  3 |  2 |  1 |  0 |  - stripes (#, width: w) and
  #  |##~~|##~~|##~~|##~~|##~~|    spaces  (~, width: w)
  #  |##~~|##~~|##~~|##~~|##~~|
  #  |##~~|##~~|##~~|##~~|##~~|
  #  '                        `-- the center of the ring
  #  `--------------------------- the end of the ring
  w = STRIPEWIDTH
  distr = []
  stripe_end = RingRadius - 1
  last = STRIPES - 1
  for i in range(STRIPES):
    stripe_beg = stripe_end - w + 1
    space_end = stripe_beg - 1
    if i == last:
      space_beg = space_end = None  # the last space will be a hole (not drawn)
    else:
      space_beg = space_end - w + 1
    it = {'stripe_beg': stripe_beg, 'stripe_end': stripe_end,
          'space_beg':  space_beg,  'space_end':  space_end}
    distr.append(it)
    if i != last:
      stripe_end = space_beg - 1
  drawn = distr[0]['stripe_end'] - distr[-1]['stripe_beg'] + 1
  hole = RingRadius - drawn
  assert hole == w, f'{hole}!={w}'
  pins_dist = RingRadius + w - 2 + ROUGHNESSFIX
  return {'distr': distr, 'pins_dist': pins_dist}

  # w = STRIPEWIDTH
  # stripe_end = -1
  # for i in range(STRIPES):
  #   space_beg = stripe_end + 1
  #   space_end = space_beg + w - 1
  #   stripe_beg = space_end + 1
  #   stripe_end = stripe_beg + w - 1
  #   it = {'stripe_beg': stripe_beg, 'stripe_end': stripe_end,
  #         'space_beg': space_beg, 'space_end': space_end}
  #   distr.append(it)
  # pins_dist = RingRadius + (w/2) + 2  # distance b/w pins
  # res = {'distr': distr, 'pins_dist': pins_dist}
  # distr = [intdict(d) for d in distr]
  # res = intdict(res)
  # return res

# def find_pie_angles(h_r, *, quadrant=1):
#   '''Finds angles of a pie used to restored bottom half of a ring.
#   It uses `h_r` - hole-radius which can be found from `stripes_distribution()`.
#   '''
#   #
#   #        Finds the angles d ("pie"), a:
#   #
#   #                ,------ central circle (hole, radius h_r)
#   #                :
#   #              +---+
#   #              :   :
#   #              :   :
#   #             .A~~~o.    <-- A(-h_r,?)       A,B can be found with
#   #           .' \a|   '.                      `circle_point()` knowing
#   #          / d  \|     \                     one coordinate.
#   #    +.....B._   \     | <-- B(?,h_r)        Pie `d` is constrainted
#   #  ,.:  a _|_(`~.o     | <-- Center:(0,0)    from the left/right by
#   #  : +.....o           /                     the same small angles (`a`).
#   #  :        '.       .'
#   #  :          `~---~'
#   #  :
#   #  `--central circle (hole, radius h_r)
#   #
#   # A_y = circle_point((0,0), RingRadius, x=-h_r)[1]
#   Bs = circle_point((0,0), RingRadius, y=h_r)
#   B_x = Bs[0]
#   B = (B_x, h_r)
#   B_eq = determine_line((0,0), B)
#   B_ang = math.degrees(math.atan(B_eq['k']))  # FIXME must be normalized coz -pi/2..pi/2
#   if B_ang < 0:
#     # math.atan() returns angle as -pi/2..+pi/2, so normalize:
#     #  \ | +180
#     #   \|<-.
#     # ---+---:--
#     #    |\.'  -x
#     #    | \
#     B_ang += 180
#   a = 180 - B_ang
#   quadrant0, quadrant1 = Quadrants[quadrant]
#   return {'a': a, 'd': (quadrant0 + a, quadrant1 - a)}

def draw_arc(dr, pt, radius, ang0, ang1, *, width=1, color='white'):
  '''`pt` - abstract cartesian coords, start/stop angels are in degrees.
  '''
  if width < 1:
    width = 1
  if isinstance(color, (tuple, list)):
    color = 'hsv(%d,%d%%,%d%%)' % color
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
    #draw_circle(dr, pc, width, fill=color, width=1) # "point" drawing the arc
    dr.point(pc, fill=color)
    ang += ang_step
  #draw(max(1, width), color)

def draw_thick_arc(dr, pt, radius, ang0, ang1, *, width=1, color='white'):
  'Draws arcs which width is greater than 1 as concentrated arcs'
  #rad0 = radius - math.ceil(width/2)
  #rad1 = radius + math.floor(width/2)
  rad0 = radius - (width//2)
  rad1 = radius + (width//2)
  for r in range(rad0, rad1 + 1):
    draw_arc(dr, pt, r, ang0, ang1, width=1, color=color)

def find_pins(distr):
  '''Returns matrix of pins as Discartes coords and matrix is:
  p, p, p...  <-- row
  p, p, p...  <-- row
  I.e., result[row][col] or result[y][x]
  '''
  #      0  1  2  3  4
  # 0    +  +  +  +  +
  # 1    +  +  +  +  +
  # 2    +  +  +  +  +
  # 3    +  +  X  +  +  <-- center: (h_mid, v_mid)
  # 4    +  +  +  +  +
  # 5    +  +  +  +  +
  dist = distr['pins_dist']
  h_num = math.ceil(SIZE[0] / dist) + 1 +1 # additional +1 for "tails"
  v_num = math.ceil(SIZE[1] / dist) + 1 +1 # additional +1 for "tails"
  res = matrix(h_num, v_num)
  h_mid = h_num//2
  v_mid = v_num//2
  # constraint values like x_0, y_0 are calculated from the middle "X"
  y_0 = v_mid * dist
  for y in range(v_num):
    x_0 = -(h_mid * dist)
    for x in range(h_num):
      res[y][x] = (x_0, y_0)
      x_0 += dist
    y_0 -= dist
  return res

def flat_2x2(mx): return [col for row in mx for col in row]

def draw_ring(dr, p, angs, distr):
  'p - cartesian, distr - distribution'
  sp_c = 'hsv(%d,%d%%,%d%%)' % tuple(RINGCOLOR)  # light, space
  st_c = 'hsv(%d,%d%%,%d%%)' % tuple(STRIPECOLOR)  # dark, stripe
  ang0, ang1 = angs
  r = 0
  for d in distr['distr']:
    if d['space_end'] is not None:
      sp_w = d['space_end'] - d['space_beg'] + 1
      r = d['space_beg'] + round(sp_w/2) - 1
      draw_thick_arc(dr, p, r, ang0, ang1, width=sp_w, color=sp_c)
    st_w = d['stripe_end'] - d['stripe_beg'] + 1
    r = d['stripe_beg'] + round(st_w/2) - 1
    draw_thick_arc(dr, p, r, ang0, ang1, width=st_w, color=st_c)

def draw_rings(dr, pins_2x2, distr):
  st_c = 'hsv(%d,%d%%,%d%%)' % tuple(STRIPECOLOR)  # dark, stripe
  cols = len(pins_2x2[0])
  mid_col = cols//2
  angs = [(0,180), (180,360)]  # rem of %2: to draw circle 1/2 :'': or :..:
  center = 0  # angs[0]
  first = center if 0 == (mid_col%2) else center^1
  for irow in range(len(pins_2x2)):
    ang_i = first
    for col in pins_2x2[irow]:
      draw_ring(dr, col, angs[ang_i], distr)
      ang_i ^= 1  # flip-flop
    if irow > 0:
      ang_i = first
      for col in pins_2x2[irow - 1]:
        if ang_i == 1:
          draw_ring(dr, col, Quadrants[3], distr)
        ang_i ^= 1  # flip-flop

# def get_draw_shadow_point(img):
#   def fn(pt):
#     pt = int(pt[0]), int(pt[1])
#     if (SIZE[0] > pt[0] > 0) and (SIZE[1] > pt[1] > 0):
#       rgb = img.getpixel(pt)
#       rgb = (rgb[0] - SHADOWDEPTH, rgb[1] - SHADOWDEPTH, rgb[2] - SHADOWDEPTH)
#       img.putpixel(pt, rgb)
#   return fn


############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
distr = stripes_distribution()
pins_2x2 = find_pins(distr)
# angs = find_pie_angles(h_r, quadrant=3)
draw_rings(dr, pins_2x2, distr)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')