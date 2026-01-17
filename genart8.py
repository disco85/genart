from PIL import Image, ImageDraw
import random
import math


OUT = 'genart8.png'
IMGBG = (18, 55, 15)  # HSV
SIZE = (1200, 900)
RADIUS = 80  # 50 allows to check correctness covering of the canvas
RINGSDENSITY = 1.4
COLOR = (30,37,100)  # HSV
FLARECOLOR = (26,0,90)  # HSV
FLARESHORTERON = 10  # degrees: how flare is shorter from left/right edges
PINCONTRAST = 20  # value,% in HSV how lighter pin is than the IMGBG
RINGWIDTH = 15
SHADOWBAND = 15
SHADOWCONTRAST = 30  # value,% in HSV of the rim darkest shadow
IMGTILT = 70  # degrees


center = (SIZE[0]//2, SIZE[1]//2)
xrng = (-SIZE[0]//2, SIZE[0]//2)  # 0x range in Descartes
yrng = (-SIZE[1]//2, SIZE[1]//2)  # 0y range in Descartes

def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def as_list(xs, **mod):
  'Converts `xs` to list and modify some items with args like _0=value/lambda'
  l = list(xs)
  for k in mod:
    try:
      assert k.startswith('_')
      i = int(k[1:])
      v = mod[k]
      l[i] = v(l[i]) if callable(v) else v
    except:
      continue
  return l

def is_outside(pts, xr, yr):
  '''Returns True if all `pts` are outside of the canvas. `xr`, `yr` are ranges
  (min, max) for 0x, 0y.
  '''
  return all(
    (p[0] < xr[0]) or (p[0] > xr[1]) or (p[1] < yr[0]) or (p[1] > yr[1])
    for p in pts)

def norm_angle(ang):
  'Normilizes angle (in usual trigonometric coordinates)'
  ang0 = ang % 360 if ang >= 360 else ang
  return 360 + ang0 if ang0 < 0 else ang0

def to_arc(ang1, ang2=None):
  r'''Converts trigonometric angle to arc-convention angle. If there is 2 angles
  then converts them to arc/chord - it must be sorted in reverse order BCS turn
  in arc-convention is clockwise (not counterclockwise like in trigonometry)

      |  .   <- 270+(90-a) in arc convention
      | . a
  ----+'---- <- arc starts here
      |\
      | `--- <- this is 45* in arc convention
  '''
  a1 = norm_angle(270 + (90 - ang1))
  if ang2 is None:
    return a1
  else:
    a2 = norm_angle(270 + (90 - ang2))
    return reversed((a1, a2))  # reversed - clockwise

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

def draw_rim(dr, p, ang0, ang1):
  'Pseudo-3D sector (rim of a ring)'
  steps = 7
  rw0 = RINGWIDTH
  rwn = 2
  rws = abs(rwn - rw0)/(steps - 1)
  ri = RADIUS
  rwi = RINGWIDTH
  c0 = SHADOWCONTRAST
  cn = 100
  cs = abs(cn - c0)/(steps - 1)
  ci = c0
  lw0 = 3
  lwn = 1
  lws = abs(lwn - lw0)/(steps - 1)
  lwi = lw0
  for i in range(steps):
    face_color = as_list(COLOR, _2=ci)
    draw_sector(dr, p, ang0, ang1,
                outer_radius=ri, inner_radius=ri-rwi,
                face_color=face_color, shadow=True,
                line_width=lwi)
    rwi -= rws
    ri -= rws/2
    ci += cs
    lw0 -= lws
  # Flare:
  flare_rad = RADIUS - (RINGWIDTH//2)
  draw_sector(dr, p, ang0 + FLARESHORTERON, ang1 - FLARESHORTERON,
              outer_radius=flare_rad+1, inner_radius=flare_rad,
              face_color=FLARECOLOR, shadow=False,
              line_width=1)

def draw_sector(dr, p, ang0, ang1, *, outer_radius=RADIUS,
                inner_radius=RADIUS-RINGWIDTH, shadow=False,
                face_color=COLOR, line_width=3):
  smooth = 5  # angle accuracy
  if ang1 < ang0:
    ang1 += 360 * (1 + (ang0 // 360)) # add N full turn like they are in ang0
  # Now make ang1 to follow ang0 (clockwise turn!), so: 120..0 is 120,121..360:
  delta_ang = abs(ang1 - ang0)
  #ang0, ang1 = map(norm_angle, (ang0, ang1))
  ang1 = ang0 + delta_ang
  #print('%s..%s: %s' % (ang0, ang1, delta_ang))
  shadow_color = as_list(face_color, _2=lambda cc: int(0.75*cc))
  sm_ang0 = ang0 * smooth
  sm_ang1 = ang1 * smooth
  for ang in range(sm_ang0, sm_ang1):
    if shadow and (ang <= sm_ang0 + SHADOWBAND or ang >= sm_ang1 - SHADOWBAND):
      fill_color = 'hsv(%d,%d%%,%d%%)' % tuple(shadow_color)
    else:
      fill_color = 'hsv(%d,%d%%,%d%%)' % tuple(face_color)
    ang = ang / smooth
    #angn = norm_angle(ang)  # don't !
    pp1 = (ang, outer_radius)
    pp2 = (ang, inner_radius)
    p1 = polar_to_cartesian(pp1, p)
    p2 = polar_to_cartesian(pp2, p)
    p1 = cartesian_to_canvas(p1)
    p2 = cartesian_to_canvas(p2)
    dr.line([p1,p2], fill=fill_color, width=line_width)

def canvas_to_cartesian(pt):
  return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def cartesian_to_canvas(pt):
  return (pt[0] + (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def draw_star(dr, p0):
  '`p0` - central point of the new/drawn star'
  sect_len = 43  # degrees
  sect_start = IMGTILT - 33  # degrees
  assert sect_len < 60, 'Sector + shadow = 60'
  radius = RINGSDENSITY * RADIUS
  for i in range(6):
    p = polar_to_cartesian((IMGTILT + i*60, radius), p0)
    #cp = cartesian_to_canvas(p)
    #dr.point(cp, fill='#0F000F')
    sect_ang = sect_start
    for j in range(6):
      draw_rim(dr, p, sect_ang, sect_ang + sect_len)
      sect_ang += (60 - sect_len) + sect_len

def draw_hexagon(dr, p0, radius, color):
  '6-edges polygon: a hexagon'
  ang = IMGTILT + 30
  ps = []
  for i in range(6):
    p = polar_to_cartesian((ang, radius), p0)
    cp = cartesian_to_canvas(p)
    ps.append(cp)
    ang += 60
  dr.polygon(ps, fill=color)

def draw_pin(dr, p0):
  'Pin - the area in the middle of rings'
  step = 10
  smooth = 4
  cs = PINCONTRAST/(step - 1)
  radius = (RINGSDENSITY*0.3) * RADIUS
  ci = as_list(IMGBG)
  for i in range(step):
    color = 'hsv(%d,%d%%,%d%%)' % tuple(ci)
    draw_hexagon(dr, p0, radius, color)
    radius -= smooth
    if radius <= 0: break
    ci[2] += cs

# def draw_wave(dr, wave=None, inner_rad=None):
#   'All rings around the center, concentration wave by wave'
#   def draw_star_and_pin(dr, p):
#     draw_pin(dr, p)
#     return draw_star(dr, p)
#   c0 = (0,0)
#   wave = wave or [c0]
#   inner_rad = inner_rad or 0
#   new_wave = set()
#   for wp in wave:
#     ps = [p for p in draw_star_and_pin(dr, wp) if distance(p, c0) > inner_rad]
#     new_wave.update(ps)
#   if not new_wave or is_outside(new_wave, xrng, yrng):
#     return
#   inner_rad = max(distance(p, c0) for p in new_wave)
#   draw_wave(dr, new_wave, inner_rad)

# def draw_sector1(dr, p, from_ang, to_ang):
#   'Arc-based sector drawing'
#   smooth = 1
#   from_ang, to_ang = to_arc(from_ang, to_ang)
#   color = list(COLOR)
#   color = 'hsv(%d,%d%%,%d%%)' % COLOR
#   for radius in range(RADIUS*smooth, (RADIUS - RINGWIDTH)*smooth, -1):
#     radius /= smooth
#     bbox_p1 = (p[0] - radius, p[1] - radius)
#     bbox_p2 = (p[0] + radius, p[1] + radius)
#     dr.arc([bbox_p1, bbox_p2], from_ang, to_ang, fill=color, width=2)

def divide_segment(p1, p2, ratio):
  '''Coordinates of new point between `p1`, `p2` dividing segment `(p1,p2)`
  in relation `ratio` - pair `(m, n)`. Segment must look as (order matters!):
  p1         div             p2
  o-----------o--------------o
       m              n                 <-- (m,n), not (n,m)!
  '''
  x1, y1 = p1
  x2, y2 = p2
  m, n = ratio
  x3 = ((m*x2) + (n*x1))/(m + n)
  y3 = ((m*y2) + (n*y1))/(m + n)
  # The same as:
  # l = m/n
  # x3 = (x1 + (l*x2))/(1+l)
  # y3 = (y1 + (l*y2))/(1+l)
  return (x3, y3)

def hexagon_points(p0, radius_mul):
  '''`p0` - central point of the hexagon, returns other points. Idea is:
  first find 6 reference points. Then divide sides (one by one) by
  `radius_mul` points
  '''
  ps = []  # centers of new circles
  # how many segments on the side/edge (1: the most inner hexagon)
  radius = RINGSDENSITY * RADIUS * radius_mul
  for i in range(6):
    p = polar_to_cartesian((IMGTILT + i*60, radius), p0)
    if i > 0:
      seg_ratio = [1, radius_mul - 1]
      ratio = seg_ratio
      for j in range(radius_mul - 1):
        pd = divide_segment(p, ps[-1 - j], ratio)
        ps.append(pd)
        ratio[0] += 1
        ratio[1] -= 1
    if i == 5:
      seg_ratio = [1, radius_mul - 1]
      ratio = seg_ratio
      for j in range(radius_mul - 1):
        pd = divide_segment(p, ps[0], ratio)
        ps.append(pd)
        ratio[0] += 1
        ratio[1] -= 1
    ps.append(p)
  return ps

def find_pins():
  'Finds all hexagons central points - aka pins'
  c0 = (0,0)
  ps = set()
  radius_mul = 1
  while True:
    hps = hexagon_points(c0, radius_mul)
    if is_outside(hps, xrng, yrng):
      break
    ps.update(hps)
    radius_mul += 1
  ps.add(c0)
  return ps

def draw_all(dr, ps):
  def draw_star_and_pin(dr, p):
    draw_pin(dr, p)
    draw_star(dr, p)
  for p in ps:
    draw_star_and_pin(dr, p)


############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
draw_all(dr, find_pins())

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')