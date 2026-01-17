# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageColor, ImageFont
import functools
import itertools
import random
import math
import pdb

OUT = 'genart13.png'
IMGBG = (26,21,0)  # HSV
SIZE = (1400, 900)
ROD = 10  # rod thickness
GRIDSTEP = 30  # step of the GRID


Center = (SIZE[0]//2, SIZE[1]//2)


def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def matrix(cols, rows, init=None):
  return [[init for col in range(cols)] for x in range(rows)]

def seq(xs, *, t=None, **mod):
  '''Converts `xs` to list/tuple, modifies items with args like _0=value/lambda
  or _=value/lambda (over all items). `t` may be not only function (like `list`),
  but a list or tuple of functions - they will be applied one by one: from the
  left to the right.
  '''
  l = list(xs)
  for k in mod:
    try:
      assert k.startswith('_')
      v = mod[k]
      if not k[1:]:
        for i in range(len(l)):
          l[i] = v(l[i]) if callable(v) else v
      else:
        i = int(k[1:])
        l[i] = v(l[i]) if callable(v) else v
    except:
      continue
  if t is None:
    return tuple(l) if isinstance(xs, tuple) else list(l)
  elif isinstance(t, (list, tuple)):
    return functools.reduce(lambda i,f:f(i), t, xs)
  else:
    return t(l)

def bound_box(ps):
  'Bound box from list of points'
  x0 = x1 = y0 = y1 = None
  for p in ps:
    if x0 is None:
      x0 = p[0]
      x1 = p[0]
      y0 = p[1]
      y1 = p[1]
    else:
      if p[0] < x0: x0 = p[0]
      elif p[0] > x1: x1 = p[0]
      if p[1] < y0: y0 = p[1]
      elif p[1] > y1: y1 = p[1]
  return [(x0,y0), (x1,y1)]

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

def hexagon(p0, radius):
  '''Hexagon Cartesian points (counter-clockwise ordered) with Cartesian
  center `p0` and `radius`. They are returned as:
  {'points':(_), 'center': _, 'radius': _}
  '''
  ang = 60
  ps = []
  for i in range(6):
    p = polar_to_cartesian((ang, radius), p0)
    ps.append(p)
    ang += 60
  bbox = bound_box(ps)
  return {'points': tuple(ps), 'center': p0, 'radius': radius, 'bbox': bbox}

# def sorted_hexagons(hs):  # FIXME sort by bbox ?
#   return sorted(hs, key=lambda h: distance(h['center'], (0,0)))

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

def is_outside(pts, *args):
  '''Returns True if all `pts` are outside of the canvas
  '''
  if len(args) == 2:
    xr, yr = args
    if not isinstance(xr, (list, tuple)): xr = (0, xr)
    if not isinstance(yr, (list, tuple)): yr = (0, yr)
  elif len(args) == 1:
    w, h = args[0]
    xr = (-w//2, w//2); yr = (-h//2, h//2)
  return all(
    (p[0] < xr[0]) or (p[0] > xr[1]) or (p[1] < yr[0]) or (p[1] > yr[1])
    for p in pts)

def points_to_segs(ps):
  '''>>> points_to_segs([1,2,3])
  [(1, 2), (2, 3)]
  '''
  p0 = None
  segs = []
  for p in ps:
    if p0 is not None:
      segs.append((p0,p))
      p0 = p
    else:
      p0 = p
  return segs

def find_pins():
  # Find pins as vertical zigzags:
  #  \  /   \
  #  /..\.../  ... central point: distance to left=3GRIDSTEP
  #  \  /   \                              to right=6GRIDSTEP
  #  /  \   /
  vstep = 3 * GRIDSTEP
  def vert_zigzag(p0, angs, lim):
    i = 0
    margin = 2
    res = []
    while margin > 0:
      ang = angs[i%2]
      p1 = polar_to_cartesian((ang, vstep), orig=p0)
      res.append(p1)
      if abs(p1[1]) > lim:
        margin -= 1
      p0 = p1
      i += 1
    return res
  def horiz_shift(p0, to_left):
    #         h_mirror:
    #
    #    /_a     \_a     b=360-a
    #    \ b     / b     a=360-b
    #
    #         v_mirror:
    #
    #              __    b=180-a
    #    \b/_a   b/\a    a=180-b
    #
    h_mir = lambda ang: 360 - ang
    v_mir = lambda ang: 180 - ang
    dup = lambda a, f: (a, f(a))
    p0 = list(p0)
    shifts = (-3*GRIDSTEP, -6*GRIDSTEP) if to_left else (6*GRIDSTEP, 3*GRIDSTEP)
    res = []
    i = 0
    ang = 60
    while True:
      res_up = vert_zigzag(p0, dup(ang, v_mir), Center[1])
      res_dn = vert_zigzag(p0, dup(h_mir(ang), v_mir), SIZE[1])
      u = is_outside(res_up, SIZE)
      d = is_outside(res_dn, SIZE)
      if u and d:
        break
      res.append(p0[:])
      res.extend(res_up)
      res.extend(res_dn)
      p0[0] += shifts[i%2]
      i += 1
      ang = v_mir(ang)
    return res
  p0 = (-vstep, 0)  # central point
  res = []
  res.extend(horiz_shift(p0, True))
  res.extend(horiz_shift(p0, False))
  uniq_res = []
  for el in res:
    if el not in uniq_res: uniq_res.append(el)
  return uniq_res

def gen_hexagons(pins):
  res = []
  for pin in pins:
    hg = hexagon(pin, radius=2*GRIDSTEP)
    res.append(hg)
  return res

def flat_2x2(mx): return [col for row in mx for col in row]

def debug(dr, ps, color='white'):
  for p in ps:
    if p is not None:
      cp = cartesian_to_canvas(p)
      dr.point(cp, fill=color)

def draw_segments(dr, segs, only_segments=None, **line_kw):
  width = line_kw.get('width', 1)
  fill = line_kw.get('fill', 'white')
  if only_segments == 'odd':
    ok_seg = lambda i: 0 != (i%2)
  elif only_segments == 'even':
    ok_seg = lambda i: 0 == (i%2)
  else:
    ok_seg = lambda i: True
  segs1 = [s for i, s in enumerate(segs, start=1) if ok_seg(i)]
  for (p0,p1) in segs1:
    dr.line((p0,p1), **line_kw)
    draw_circle(dr, p0, width/2 - 1, fill=fill, width=1)
    draw_circle(dr, p1, width/2 - 1, fill=fill, width=1)

def draw_hexagon(dr, hg, only_segments=None):
  '''Segments are drawn from point 1: 1,2,3,4,5,6,7. Segments
  are numerated by their first point, so: 1st segment is (1,2),
  the 2nd: (2,3)... the last is 6th: (6,7).
  `only_segments` can be None (all), 'odd', 'even'
  '''
  #         0
  #
  #       2--1,7   5
  #  1   /      \
  #     3        6
  #     \       /
  #  2    4---5    4
  #
  #         3
  #segs = itertools.pairwise(hg['points'])
  ps = [cartesian_to_canvas(p) for p in hg['points']]
  ps.append(ps[0])
  # pdb.set_trace()
  width = ROD + 4
  color = 'yellow'
  ps_segs = points_to_segs(ps)
  draw_segments(dr, ps_segs, only_segments=only_segments, fill=color, width=width)
  #dr.line(ps, fill=color, width=width)
  # for p in ps:
  #   draw_circle(dr, p, width/2 - 1, fill='yellow', width=1)
  width = ROD
  color = 'green' #'yellow' if only_segments=='odd' else 'green' #'red'
  draw_segments(dr, ps_segs, only_segments=only_segments, fill=color, width=width)
  # dr.line(ps, fill=color, width=width)
  # for p in ps:
  #   draw_circle(dr, p, width/2 - 1, fill='red', width=1)

def even(i): return 0 == (i%2)
def odd(i): return 0 != (i%2)

def symmetric_enumerate(elems, elems_num=None, prefer_to_left=True):
  '''Generator as `enumerate()` but indexes are symmetric: -2,-1,0,1,2. If `elems`
  are iterator then `elems_num` should be provided. `prefer_to_left` determines
  how to treat [10,20] case: when it is True: -1, 0, else: 0, 1.
  '''
  num = elems_num or len(elems)
  half = num // 2
  rest = num % 2
  if rest:
    mid = half
  elif prefer_to_left:
    mid = half - 1
  else:
    mid = half
  for i, el in enumerate(elems):
    yield (i - mid, el)

def draw_hexagons(dr, hgs):
  fst = lambda a: a[0]
  by_0x = lambda hg: int(hg['center'][0])
  by_0y = lambda hg: int(hg['center'][1])
  # sorted lines from the bottom to up: points inside lines are sorted by 0x:
  hg_mx = [sorted(ln, key=by_0x) for k,ln in itertools.groupby(sorted(hgs, key=by_0y), key=by_0y)]
  font = ImageFont.truetype('/home/nothome/prj/shared/algs/font1.ttf', size=18)
  for y,hg_line in symmetric_enumerate(hg_mx):
    # print(len(hg_line))
    y_beg = True
    x_beg = y_beg
    for x,hg in symmetric_enumerate(hg_line):  # over columns/over 0X
      only_segments = 'even' if x_beg else 'odd'
      draw_hexagon(dr, hg, only_segments=only_segments)
      dr.text(cartesian_to_canvas(hg['center']), f'{x}:{y}', font=font, fill='white')
      x_beg = not x_beg
    y_beg = not y_beg
  # for hg in hgs:
  #   draw_hexagon(dr, hg, only_segments='odd')

############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
x = [1,2,3,4,[5,6]]
pins = find_pins()
hgs = gen_hexagons(pins)
draw_hexagons(dr, hgs)
# debug(dr, ps)
# debug(dr, flat_2x2(pins_2x2))
# draw_arc(dr, canvas_to_cartesian(Center), 200, 0, 360, draw_point=draw_ring_point())
# draw_arc(dr, canvas_to_cartesian(Center), 100, 0, 360, draw_point=draw_ring_point(True))

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')
