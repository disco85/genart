# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageColor
import random
import math
import pdb

OUT = 'genart10.png'
IMGBG = (36,31,80)  # HSV
SIZE = (1400, 800)
RINGRADIUS = 80
STRIPES = 4
SPACEWIDTH = 0.7  # space b/w stripes as percentage of a stripe's width
RINGCOLOR = (36,31,80)  # HSV
STRIPECOLOR = (26,39,21)  # HSV
SHADOWS = True
SHADOWMAXLEN = 0.06  # multiplier of RANDRADIUS
# Degrees: it's an angle b/w a plumb from the center of a ring and the
# cross point with an another ring:
#   '       '
#  '    .    '
#  :   /|    :
#  '. / |   .'
#    o..|..'
CROSSANGLE = 7

assert 1 < CROSSANGLE < 45, 'Invalid CROSSANGLE value'
assert 1 < STRIPES, 'Invalid STRIPES value'


def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def gap_side():
  r'''Finds the approximate gap (between rings) side, it's 2*b,
  see the figure:

     '       '
    '    .p0  '  <-- p0=(0,0)
    :   /|    :
    '. /`| a .'  <-- angle (p2,p0,1) is CROSSANGLE
      /_[|..'    <-- a=RINGRADIUS
     ' b `--- p1
     `------- p2

  tg(CROSSANGLE) = b/a  =>  b = a*tg(CROSSANGLE)
  '''
  b = math.tan(math.radians(CROSSANGLE)) * RINGRADIUS
  return b*2

GapSide = gap_side()
# Horiz/vertic distance b/w ring centers:
PinsOrthogonalDist = GapSide + (2*RINGRADIUS)


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
  r'''Converts polar coordinates (angle, radius) to abstract Descartes (x,y)
  if `orig` is None or to real/global Descrates if `orig` points out the
  real cartesian coordinates of the origin point of the polar turning:

   x,y...|
         |^  ang
  orig...|.\.___    Polar coord  (ang,dist) - vector tip is "x"
         | /:
         |/_:_____
       0,0  :
          orig
  '''
  ang, rad = pp
  ang = math.radians(ang)
  x = rad * math.cos(ang)
  y = rad * math.sin(ang)
  ox, oy = (0,0) if orig is None else orig
  # if to return int-s I hit strange error with multiple points very close
  # to each others, like additive error:
  return (x + ox, y + oy)

def cartesian_to_polar(p, orig=None):
  r'''
   x,y...|
         |^  ang
  orig...|.\.___    Polar coord  (ang,dist) - vector tip is "x"
         | /:
         |/_:_____
       0,0  :
          orig
  '''
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

# def canvas_to_cartesian(pt):
#   return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def cartesian_to_canvas(pt):
  return (pt[0] + (SIZE[0]/2), (SIZE[1]/2) - pt[1])

def affine(p, mx):
  x,y = p
  ((a,b,c), (d,e,f)) = mx
  x1 = a*x + b*y + c
  y1 = d*x + e*y + f
  return (x1, y1)

def circle_pt(cp, radius, *, x=None, y=None):
  '''Returns x or y from y or x of the circle with a center `cp`:
  (x-cx)^2 + (y-cy)^2 = R^2
  (y-cy) = +/-sqrt(R^2 - (x-cx)^2) => y = cy +/- sqrt(R^2 - (x-cx)^2)
  (x-cx) = +/-sqrt(R^2 - (y-cy)^2) => x = cx +/- sqrt(R^2 - (y-cy)^2)
  '''
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

def draw_circle(dr, p, radius, **kw):
  l = p[0] - radius
  r = p[0] + radius
  t = p[1] - radius
  b = p[1] + radius
  dr.ellipse((l,t,r,b), **kw)

def draw_arc(dr, pt, radius, ang0, ang1, *, width=1, color='white', aa=False):
  '''`pt` - abstract cartesian coords, start/stop angels are in degrees.
  `color` as HSV tuple if antialiasing (`aa`=True) is needed.
  '''
  def draw(width, color):
    '''Common draw (for antialiasing): `width` is radius of small circles -
    they simulate "width" of the arc-line'''
    nonlocal ang0, ang1
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
  if aa and isinstance(color, (tuple, list)):
    c1 = seq(color, t=tuple, _2=lambda c: max(1, c - (c//3)))
    c2 = seq(color, t=tuple, _2=lambda c: c)
    c1 = 'hsv(%d,%d%%,%d%%)' % c1
    c2 = 'hsv(%d,%d%%,%d%%)' % c2
    draw(max(1, width), c1)
    draw(max(1, (width) - 2), c2)
  else:
    if isinstance(color, (tuple, list)):
      color = 'hsv(%d,%d%%,%d%%)' % color
    draw(max(1, width), color)

def draw_thick_arc(dr, pt, radius, ang0, ang1, *, width=1, color='white'):
  'Draws arcs which width is greater than 1 as concentrated arcs'
  rad0 = round(radius - (width/2))
  rad1 = round(radius + (width/2))
  for r in range(rad0, rad1 + 1):
    draw_arc(dr, pt, r, ang0, ang1, width=1, color=color, aa=False)

def find_pins():
  '''Returns matrix of pins as Discartes coords and matrix is:
  p, p, p...  <-- row
  p, p, p...  <-- row

  I.e., result[row][col] or result[y][x]
  '''
  ort2 = PinsOrthogonalDist//2
  h_num = math.ceil(SIZE[0] / PinsOrthogonalDist)
  v_num = math.ceil(SIZE[1] / PinsOrthogonalDist)
  def pins_from_center(y):
    lps = []; rps = []
    for i in range(0, (h_num//2) + 1):
      lps.insert(0, (-(i*PinsOrthogonalDist), y))
      rps.append(   ( (i*PinsOrthogonalDist), y))
    return lps + rps
  def pins_not_from_center(y):
    lps = []; rps = []
    for i in range(0, ((h_num - 1)//2) + 1):
      lps.insert(0, (-((i*PinsOrthogonalDist) + ort2), y))
      rps.append(   (  (i*PinsOrthogonalDist) + ort2, y))
    return lps + rps
  tps = []; bps = []
  for v in range(0, v_num + 1):
    if v % 2:
      tps.insert(0, pins_from_center(v*ort2))
      bps.append(   pins_from_center(-v*ort2))
    else:
      tps.insert(0, pins_not_from_center(v*ort2))
      bps.append(   pins_not_from_center(-(v*ort2)))
  return tps + bps

def flat_2x2(mx): return [col for row in mx for col in row]

def draw_ring(dr, p, angs):
  'p - cartesian'
  c1 = 'hsv(%d,%d%%,%d%%)' % tuple(RINGCOLOR)
  c2 = 'hsv(%d,%d%%,%d%%)' % tuple(STRIPECOLOR)
  spaces = STRIPES - 1
  whole = RINGRADIUS
  ang0, ang1 = angs
  last_space_div = 1
  # If w: width of a stripe, s: width of a space, then
  # STRIPES*w + spaces*(w*SPACEWIDTH) + (w*SPACEWIDTH/8)= whole
  # => w = whole/(STRIPES + spaces*SPACEWIDTH + SPACEWIDTH/2)
  #
  # <---- RINGRADIUS ---->
  # |                    |
  # | w s w s w s w s w ?|
  # |##::##::##::##::##..|
  # |##::##::##::##::##..|
  # |##::##::##::##::##..|
  # '                  ' `-- the center of the ring
  # '                  `---- ? = SPACEWIDTH / last_space_div
  # `----------------------- the end of the ring
  w = int(whole/(STRIPES + (spaces*SPACEWIDTH) + (SPACEWIDTH/last_space_div)))
  s = int(w * SPACEWIDTH)
  r = RINGRADIUS - (w/2)
  for i in range(STRIPES):
    last = (i == STRIPES - 1)
    s1 = s/last_space_div if last else s
    draw_thick_arc(dr, p, r, ang0, ang1, width=w, color=c2)
    draw_thick_arc(dr, p, r - (w/2) - (s1/2), ang0, ang1, width=s1, color=c1)
    r = r - w - s1
  draw_circle(dr, cartesian_to_canvas(p), w*0.75, fill=c2)

def draw_rings(dr, pins):
  for p in pins:
    draw_ring(dr, p, (0,360))

def draw_order(dr, mx):
  rows_2 = len(mx) // 2
  restore_quadrants = [3, 4]
  for i, row in enumerate(reversed(mx)):  # from bottom to top
    ii = i - 1 if i >= rows_2 else i
    restore_quadrant = restore_quadrants[ii%2]
    for j, p in enumerate(row):
      draw_ring_shadow(dr, p, restore_quadrant)
      ang0, ang1 = arc_angle(restore_quadrant)
      draw_ring(dr, p, (ang0,ang1))

def random_inside_circle(radius, density=10):
  density = int(density)
  res = []
  for _i in range(density):
    x = random.randint(-radius, radius)
    yrange = circle_pt((0,0), radius, x=x)
    yrange = list(map(int, yrange))
    if yrange[0] == yrange[1]:
      y = yrange[0]
    else:
      y = random.randint(*map(round, yrange))
    res.append((x,y))
  return res

def draw_ring_shadow(dr, p, quadrant):
  if not SHADOWS:
    return
  #cc = cartesian_to_canvas(p)
  #draw_circle(dr, cc, 3, fill='red')
  color = 'hsv(%d,%d%%,%d%%)' % tuple(STRIPECOLOR)
  ang0, ang1 = arc_angle(quadrant)
  ang0 += 5; ang1 -= 5
  arc_degrees = ang1 - ang0  # ang1 > ang0
  shadow_zones = arc_degrees // 2
  zone_r0 = 2
  zone_r1 = RINGRADIUS * SHADOWMAXLEN
  # zone_r1 will be reached for shadow_zones/2 steps bcs it grows to 1/2 then shrinks
  zone_r_step = (zone_r1 - zone_r0) / (shadow_zones/2)
  ang_step = arc_degrees / shadow_zones
  ang = ang0
  zone_r = zone_r0
  for i in range(shadow_zones + 1):
    zone_c = polar_to_cartesian((ang, zone_r + RINGRADIUS), p)
    if zone_r:
      rndps = random_inside_circle(int(zone_r), density=max(1, zone_r**2))
    else:
      rndps = [(0,0)]
    for rndp in rndps:
      cp = (rndp[0] + zone_c[0], rndp[1] + zone_c[1])
      cp = cartesian_to_canvas(cp)
      #draw_circle(dr, cp, 2, fill=color)
      dr.point(cp, fill=color)
    #zone_cc = cartesian_to_canvas(zone_c)
    #draw_circle(dr, zone_cc, zone_r, fill='green')
    # next iteration:
    if i < shadow_zones//2:
      zone_r += zone_r_step
    else:
      zone_r -= zone_r_step
    ang += ang_step

def draw_gaps_shadow(dr, pins):
  if not SHADOWS:
    return
  color = 'hsv(%d,%d%%,%d%%)' % tuple(STRIPECOLOR)
  gapside_2 = GapSide//2
  gap_r = round(gapside_2 * 1.2)
  rndps = random_inside_circle(gap_r, density=max(1, 8*(gap_r**2)))
  for row in pins:
    for p in row:
      gap_c = (p[0] + RINGRADIUS + gapside_2, p[1])
      for rndp in rndps:
        cp = (rndp[0] + gap_c[0], rndp[1] + gap_c[1])
        cp = cartesian_to_canvas(cp)
        dr.point(cp, fill=color)

def arc_angle(quadrant):
  '''Returns the angle of arc (in degrees) to restore the down ring part
  so it becomes upper. Returned angle is `(from_angle, to_angle)` in the
  counterclockwise order (like quadrants). Quadrants are 1,2,3,4:
     2 | 1
    ---+---
     3 | 4
  '''
  if quadrant == 1:
    return (CROSSANGLE, 90 - CROSSANGLE)
  elif quadrant == 2:
    return (90 + CROSSANGLE, 180 - CROSSANGLE)
  elif quadrant == 3:
    return (180 + CROSSANGLE, 270 - CROSSANGLE)
  elif quadrant == 4:
    return (270 + CROSSANGLE, 360 - CROSSANGLE)
  else:
    raise ValueError('Invalid quadrant value')

def debug(dr, ps, color='white'):
  for p in ps:
    cp = cartesian_to_canvas(p)
    draw_arc(dr, p, RINGRADIUS, 0, 360, width=5, color=(0,0,100), aa=0)
    #draw_circle(dr, cp, RINGRADIUS, fill='white')
    #dr.point(p, fill='red')

############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
pins_2x2 = find_pins()
pins = flat_2x2(pins_2x2)
draw_gaps_shadow(dr, pins_2x2)
draw_rings(dr, pins)
draw_order(dr, pins_2x2)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')