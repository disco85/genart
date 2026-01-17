from PIL import Image, ImageDraw, ImageColor
import math


OUT = 'genart9.png'
IMGBG = (0, 0, 100)  # HSV
SIZE = (1400, 800)
COLOR = (18, 55, 15)  # HSV
CROSSSIDE = 80
PENWIDTH = 10
SINMAGN = CROSSSIDE/5

# x<0: -3*sin(sqrt(-x)), x>0: 3*sin(sqrt(x))

Sqrt2 = math.sqrt(2)

def square_diag(a): return a * Sqrt2

SqDiag = square_diag(CROSSSIDE)

def seq(xs, **mod):
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
  return tuple(l) if isinstance(xs, tuple) else list(l)

def cut_uneven_edges():
  'Changes SIZE to be more relevant to CROSSSIDE'
  global SIZE
  cols = SIZE[0] // CROSSSIDE
  rows = SIZE[1] // CROSSSIDE
  SIZE = (cols*CROSSSIDE, rows*CROSSSIDE)

cut_uneven_edges()

# def canvas_to_cartesian(pt):
#   return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def cartesian_to_canvas(pt):
  return (pt[0] + (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def affine(p, mx):
  x,y = p
  ((a,b,c), (d,e,f)) = mx
  x1 = a*x + b*y + c
  y1 = d*x + e*y + f
  return (x1, y1)

def get_sin(magn=SINMAGN, half_period=SqDiag/2):
  '''Returns a function (as {'fn':sin, 'domain':_}) which will be used to
  calculate points of the 1/2 cross side (aka swastika's ray). Coords will
  be abstract.
  '''
  domain = (-int(half_period), int(half_period))
  fn = lambda x: magn * math.sin(x * math.pi/half_period)
  table = {x:fn(x) for x in range(domain[0], domain[1]+1, 1)}
  return {'fn': lambda x: table[x], 'domain': domain}

def rays_points(orig=None, get_func=get_sin):
  sin = get_func()
  sin_ps = []
  x = sin['domain'][0]
  while x <= sin['domain'][1]:
    y = sin['fn'](x)
    sin_ps.append((x,y))
    x += 1
  a1 = math.radians(45)
  a2 = a1 + math.radians(90)
  ox, oy = orig or (0,0)
  rots = []
  for a in (a1, a2):
    rots.append([[math.cos(a), -math.sin(a), ox],
                 [math.sin(a), math.cos(a), oy]])
  ps = []
  for rot in rots:
    ps.extend(affine(p, rot) for p in sin_ps)
  return ps

def draw_circle(dr, p, radius, antialiasing=True, **kw):
  l = p[0] - radius
  r = p[0] + radius
  t = p[1] - radius
  b = p[1] + radius
  dr.ellipse((l,t,r,b), **kw)

def draw_cross(dr, ps):
  radius = PENWIDTH
  fill = 'hsv(%d,%d%%,%d%%)' % COLOR
  for p in ps:
    cp = cartesian_to_canvas(p)
    draw_circle(dr, cp, radius, fill=fill)

def draw_crosses(dr, pins, **kw):
  for pin in pins:
    ps = rays_points(orig=pin, get_func=get_sin)
    draw_cross(dr, ps, **kw)

def draw_gradient_bg(dr):
  'Draws gradient background by nested rectangles'
  center = (SIZE[0]//2, SIZE[1]//2)
  n = 2  # ratio of the whole canvas area to final rectangle area
  aspect = SIZE[0] / SIZE[1]
  s_n = SIZE[0] * SIZE[1]
  h_0 = round(math.sqrt(s_n / (n*aspect)))
  steps = SIZE[1] - h_0 + 1
  v_n = IMGBG[2]
  v = COLOR[2]
  cs = (v_n - v + 1) / steps
  for h in range(SIZE[1], h_0, -1):
    w = aspect * h
    x1 = center[0] - (w/2)
    x2 = center[0] + (w/2)
    y1 = center[1] - (h/2)
    y2 = center[1] + (h/2)
    color = 'hsv(%d,%d%%,%d%%)' % seq(COLOR, _2=v)
    dr.rectangle([(x1,y1), (x2,y2)], fill=color)
    v += cs

def find_pins(_step=None):
  'Centers of crosses/swastikas in Descartes coords'
  ps = []
  half_of_cols = (SIZE[0] // CROSSSIDE) // 2
  half_of_rows = (SIZE[1] // CROSSSIDE) // 2
  step = _step or CROSSSIDE
  for row in range(0, half_of_rows+1):
    y = row * step
    for col in range(0, half_of_cols+1):
      x = col * step
      p1 = (-x, -y)
      p2 = (x, -y)
      p3 = (-x, y)
      p4 = (x, y)
      ps.extend(list({p1,p2,p3,p4}))
  return ps

# def debug(dr, ps, color='white'):
#   for p in ps:
#     dr.point(p, fill=color)

############################## draw ####################################
img = Image.new("RGB", SIZE, 'hsv(%d,%d%%,%d%%)' % IMGBG)
dr = ImageDraw.Draw(img)
draw_gradient_bg(dr)
ps = find_pins()
draw_crosses(dr, ps)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')