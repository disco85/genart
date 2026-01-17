from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
from math import *

OUT = 'genart3.png'
IMGBG = (0, 0, 0)
SIZE = (1200, 900)
def ANOMALY1(x):
  return (100*sin(x/10)/sqrt(x), (10, 100)) if x > 0 else None
def ANOMALY2(x):
  return (100*sin(-x/10)/sqrt(-x), (-10, 100)) if x < 0 else None
ANOMALIES = [ANOMALY1, ANOMALY2]
ANOMALYCOLOR = '#ffffff'
SENSITIVITY = 300
RING = 50
LINEHEIGHT = 7
LINECOLOR = '#ff00ff'
TEXT = 'VAPOR'
TEXTCOLOR = '#ffffff'
FONTSIZE = 200
FONTNAME = 'msyhbd.ttc'
COMPOSITIONPADDING = (40, 40)

#def rnd(x, tolerance=None, step=None):
#  if not tolerance:
#    return x
#  else:
#    return random.randrange(x - tolerance, x + tolerance, step or 1)

def toaxis(pt):
  return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def fromaxis(x, y):
  return (x + (SIZE[0]//2), (SIZE[1]//2) - y)

def dist(pt1, pt2):
  return int(sqrt(((pt2[0] - pt1[0])**2) + ((pt2[1] - pt1[1])**2)))

def draw_lines(dr):
  hstep = 1
  vstep = LINEHEIGHT
  padding = COMPOSITIONPADDING
  domain = SIZE[0] - 2*padding[0]  # just half of domain actually
  codomain = SIZE[1] - 2*padding[1]  # just half of codomain actually
  ypts = [None] * len(ANOMALIES) # each anomaly's version of points' 0y-s
  for y in range(-codomain, codomain, vstep):
    for x in range(-domain, domain, hstep):
      for anom_i, anomaly in enumerate(ANOMALIES):
        y1 = y
        if (anom := anomaly(x)):
          anom_y, anom_off = anom
          anom_dist = max(1, dist((x,y), anom_off))
          if anom_dist < SENSITIVITY:
            pen_color = ANOMALYCOLOR
            y1 = y + anom_y*(RING/anom_dist)
          else:
            pen_color = LINECOLOR
        else:
          pen_color = LINECOLOR
          anom_dist = -1
        ypts[anom_i] = (y1, pen_color)
      # select first 0y that is different than 0y w/o anomaly. If no one
      # then use any (default, the 0-th, eg.):
      (y1, pen_color) = next((p for p in ypts if p[0]!=y), ypts[0])
      pt = fromaxis(x, y1)
      dr.point(pt, fill=pen_color)

def draw_text(dr, img):
  background = Image.new("RGBA", img.size, (0, 0, 0))
  mask = Image.new("RGBA", img.size, (0,0,0,123))
  draw = ImageDraw.Draw(mask)
  font = ImageFont.truetype(FONTNAME, FONTSIZE)
  txt_len = dr.textlength(TEXT, font=font)
  center_x = SIZE[0] // 2
  bottom = SIZE[1] - COMPOSITIONPADDING[1] - 2*FONTSIZE  # under the padding
  pt = (center_x - (txt_len//2), bottom)
  draw.text(pt, TEXT, fill=TEXTCOLOR, font=font)
  new_img = Image.composite(img, background, mask)
  return new_img


############################## draw ####################################
img = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(img)
draw_lines(dr)
img = draw_text(dr, img)
# Save result
with open(OUT, 'wb') as f:
  img.save(f, format='PNG')