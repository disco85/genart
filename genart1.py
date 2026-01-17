from PIL import Image, ImageDraw, ImageFont, ImageColor
import random

IMGBG = (40,20,2)
SIZE = (1024, 768)
SQSIDE = 10
DECIMATION = 3  # skip every N square
SQCOORDTOLERANCE = 5
WIDTHTOLERANCE = 2
PENCOLOR = (90,64,20)  # HSL(h, s%, l%) - Hue-Saturation-Lightness
BRUSHCOLOR = (54,27,21) # the same format
LAYERDIST = 5  # distance between layers in squares

def rnd(x, tolerance=None, positive=True):
  if tolerance is None: res = x
  else: res = random.randint(x - tolerance, x + tolerance)
  return abs(res) if positive else res

def square_coord(col, row, sqside=SQSIDE):
  return [(col*sqside, row*sqside),
          ((col+1)*sqside, (row+1)*sqside)]

class Layer:
  def __init__(self, i):
    self.sqside = 10 + 4*i #4 + (7*i)
    cols = SIZE[0] // self.sqside
    rows = SIZE[1] // self.sqside
    padding = i * LAYERDIST
    self.cols = list(range(1 + padding, cols - 1 - padding))
    self.rows = list(range(1 + padding, rows - 1 - padding))
    self._pencolor = (50*i, 10 + 10*(3-i), 4 + 6*i)
    self._brushcolor = (24 + i*10, 10*(3-i), 25 + 10*i)
  @property
  def pencolor(self):
    return (self._pencolor[0],
            rnd(self._pencolor[1], 10), #50),
            rnd(self._pencolor[2], 30))
  @property
  def brushcolor(self):
    return (self._brushcolor[0],
            rnd(self._brushcolor[1], 70), #50),
            rnd(self._brushcolor[2], 10))

def draw_square(dr, coords, **opts):
  dr.rectangle(coords, **opts)

def draw_layer(dr, layer):
  for col in layer.cols:
    for row in layer.rows:
      if random.randint(0, 20) % DECIMATION:
        continue
      coords = square_coord(col, row, layer.sqside)
      coords = [(rnd(x, SQCOORDTOLERANCE),
                 rnd(y, SQCOORDTOLERANCE)) for x,y in coords]
      outline2 = 'hsl(%d,%d%%,%d%%)' % layer.pencolor
      fill2 = 'hsl(%d,%d%%,%d%%)' % layer.brushcolor
      draw_square(dr, coords, width=rnd(1, WIDTHTOLERANCE),
                  fill=fill2, outline=outline2)

im = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(im)
for l in [0,1,2]:
  draw_layer(dr, Layer(l))

# Save result
with open('genart1.png', 'wb') as f:
  im.save(f, format='PNG')