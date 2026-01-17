from PIL import Image, ImageDraw, ImageFont, ImageColor
import random

OUT = 'genart2.png'
IMGBG = (0, 0, 0)
SIZE = (1200, 1000)
CELLSIZE = 80
STARTSTEPS = 500
LAYERS = 15
PENCOLOR = (150,50,90)  # HSL
CIRCLERADIUS = 100
CIRCLEDENSITY = 5
CIRCLECOLORS = [(295, 65, 10), (223, 65, 10)]
TEXT = 'T  E  C  H  N  O'
TEXTCOLOR = 'hsl(330,63%,58%)'
FONTNAME = 'Circuitboard.otf'
FONTSIZE = 120
RAYS = 10  # rays number in each direction


Up, Down, Left, Right = range(4)  # directions

def rnddir(): return random.randint(0, 3)

def dir2coord(pt, dir, step=CELLSIZE):
  if dir == Up:      return (pt[0],                      max(1, pt[1] - step))
  elif dir == Left:  return (max(1, pt[0] - step),       pt[1])
  elif dir == Down:  return (pt[0],                      min(SIZE[1], pt[1] + step))
  elif dir == Right: return (min(SIZE[0], pt[0] + step), pt[1])
  else: assert 0

def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

class Layer:
  def __init__(self, i):
    self.i = i
    i1 = i + 1
    #i1r = i1//2
    #self.pen_color = (90*i1r, 90*i1r, 100)
    self.pen_width = 1 #random.randint(i1, i1*2)
    self.x_tolerance = (SIZE[0] // 2) - (i*40)
    self.y_tolerance = (SIZE[1] // 2) - (i*40)
    self.cellsize = CELLSIZE//i1
    self.line_segments = random.randint(2, i1*2)
    self.steps = STARTSTEPS*min(1, 10-i)
  @property
  def pen_color(self):
    c = list(PENCOLOR)
    c[0] = abs(rnd(c[0], 120, 20))
    c[2] = abs(rnd(c[1], 150, 25))
    c[2] = abs(rnd(c[2], 100, 20))
    return 'rgb(%d,%d,%d)' % tuple(c)

def draw_lines(dr, layer):
  center_x = SIZE[0] // 2
  center_y = SIZE[1] // 2
  for step in range(layer.steps):
    pt0 = (rnd(center_x, layer.x_tolerance, layer.cellsize),
           rnd(center_y, layer.y_tolerance, layer.cellsize))
    pts = []
    for i in range(layer.line_segments):
      dir = rnddir()
      pts.append(dir2coord(pt0, dir, layer.cellsize))
    dr.line(pts, fill=layer.pen_color, width=layer.pen_width)

def draw_circles(dr):
  center_x = SIZE[0] // 2
  center_y = SIZE[1] // 2
  for step in range(STARTSTEPS):
    if 0 == step % CIRCLEDENSITY: continue
    radius = random.randint(5, CIRCLERADIUS)
    pt0 = (rnd(center_x, center_x - radius + 1),
           rnd(center_y, center_y - radius+ 1))
    pt1 = (pt0[0] + radius, pt0[1] + radius)
    pts = [pt0, pt1]
    pen_color = list(random.choice(CIRCLECOLORS))
    pen_color[2] = abs(rnd(pen_color[2], 10))
    pen_color = 'hsl(%d,%d%%,%d%%)' % tuple(pen_color)
    dr.ellipse(pts, fill=pen_color)

def draw_text(dr):
  font = ImageFont.truetype(FONTNAME, FONTSIZE)
  txt_len = dr.textlength(TEXT, font=font)
  center_x = SIZE[0] // 2
  center_y = SIZE[1] // 2
  pt = (center_x - (txt_len//2), center_y - (FONTSIZE//2))
  dr.text(pt, TEXT, font=font, fill=TEXTCOLOR)

im = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(im)
draw_circles(dr)
for l in range(LAYERS):
  draw_lines(dr, Layer(l))
draw_text(dr)

# Save result
with open(OUT, 'wb') as f:
  im.save(f, format='PNG')