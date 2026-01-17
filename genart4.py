from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
from math import *

OUT = 'genart4.png'
IMGBG = (0, 0, 0)
SIZE = (900, 900)
CELLSIDE = 25
CELLCOLOR = (380, 30, 51)  # HSL
CELLCOLORMINLIGHT = 1  # minimal value of L (%) in HSL
CELLCOLORMAXLIGHT = 80  # maximal value of L (%) in HSL

LeftTilt, RightTilt = range(2)

assert SIZE[0]==SIZE[1], 'This artwork must be square'

def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def toaxis(pt):
  return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def fromaxis(x, y):
  return (x + (SIZE[0]//2), (SIZE[1]//2) - y)

def dist(pt1, pt2):
  return int(sqrt(((pt2[0] - pt1[0])**2) + ((pt2[1] - pt1[1])**2)))

def draw_rhomb(dr, col, row, tilt, color):
  'Tilt is a float <, > 0 (left, right tilt) and is < 1.0 - a part of CELLSIDE'
  tlx = col * CELLSIDE  # (left,top) of the cell
  tly = row * CELLSIDE
  d = int(abs(tilt) * CELLSIDE)
  if tilt < 0:  # left tilt: \
    rx1 = tlx + (CELLSIDE - d)
    ry1 = tly + d
    rx2 = tlx + d
    ry2 = tly + (CELLSIDE - d)
    brx = tlx + CELLSIDE  # (bottom, right) of the cell
    bry = tly + CELLSIDE
    pts = [(tlx,tly), (rx1, ry1), (brx, bry), (rx2,ry2)]
    dr.polygon(pts, fill=color)
  elif tilt > 0:  # right tilt: /
    rx1 = tlx + d
    ry1 = tly + d
    rx2 = tlx + (CELLSIDE - d)
    ry2 = tly + (CELLSIDE - d)
    trx = tlx + CELLSIDE  # (top, right) of the cell
    bly = tly + CELLSIDE  # (bottom, left) of the cell
    pts = [(rx1,ry1), (trx,tly), (rx2,ry2), (tlx,bly)]
    dr.polygon(pts, fill=color)

def draw_rhombs(dr):
  # XXX not parameter: it's const allowed range of the tilt of draw_rhomb()
  DRANGE = (0.5, 0)
  drange_len = abs(DRANGE[0] - DRANGE[1])
  ncols = SIZE[0] // CELLSIDE
  nrows = SIZE[1] // CELLSIDE
  center_x = SIZE[0] / 2
  center_y = SIZE[1] / 2
  # XXX better not diagonal for the full scale, but just width/2:
  diag_len = center_y #*sqrt(2.)
  for row in range(ncols+1):
    for col in range(nrows+1):
      pt = ((col*CELLSIDE) + (CELLSIDE/2),
            (row*CELLSIDE) + (CELLSIDE/2))
      center_dist = dist((center_x,center_y), pt)
      # center_dist        x
      # ----------- = ----------  => x = (center_dist * drange_len) / diag_len
      #   diag_len    drange_len
      d = (center_dist * drange_len) / diag_len
      d = min(max(DRANGE), d)
      cl = list(CELLCOLOR)
      cl[2] = (abs(center_y - center_dist) * 100) / diag_len
      cl[2] = max(CELLCOLORMINLIGHT, cl[2])
      cl[2] = min(CELLCOLORMAXLIGHT, cl[2])
      cl = 'hsl(%d,%d%%,%d%%)' % tuple(cl)
      draw_rhomb(dr, col, row, -d, cl)


############################## draw ####################################
img = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(img)
draw_rhombs(dr)
# Save result
with open(OUT, 'wb') as f:
  img.save(f, format='PNG')