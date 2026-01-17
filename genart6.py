from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
from math import *


OUT = 'genart6.png'
IMGBG = (0, 0, 0)
SIZE = (1200, 900)
RADIUS = 450
STICKS = 1800
ANGLERANGE = radians(0.5)
STICKCOLOR = [24,100,36]  # HSL
SEGMENTLEN = 5  # length of a color segment in pixels


center = (SIZE[0] // 2, SIZE[1] // 2)
radius_segments = RADIUS//SEGMENTLEN
light_step = 5*(STICKCOLOR[2] / radius_segments)

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

def det_line(p1, p2):
  '''Determines the equation on 2 points as (k,b). If it is a vertical line,
  return (float('inf'), x)'''
  x1,y1 = p1; x2,y2 = p2
  if x1 != x2:
    k = (y1 - y2) / (x1 - x2)
    b = y2 - k*x2
  else:
    k = inf
    b = x1
  return (k, b)

def pol2dec(pp):
  'Converts polar coordinates (angle, radius) to Descartes (x,y)'
  ang, rad = pp
  x = rad * cos(ang)
  y = rad * sin(ang)
  #print('ang=%.2f rad=%d x=%d y=%d cos=%.2f sin=%.2f' % (ang,rad,x,y,cos(ang),sin(ang)))
  return fromaxis(x, y)

def draw_segment(dr, pp0, seg_color):
  mid_ang, tip_rad = pp0
  angs = [mid_ang + ANGLERANGE, mid_ang - ANGLERANGE]
  rads = [tip_rad, tip_rad - SEGMENTLEN]
  pps = [(angs[0], rads[0]), (angs[1],rads[0]),(angs[1],rads[1]),(angs[0],rads[1]),
         (angs[0], rads[0])]
  dps = [pol2dec(pp) for pp in pps]
  color = 'hsl(%d,%d%%,%d%%)' % seg_color
  dr.polygon(dps, fill=color, outline=color)

def draw_stick(dr, pp0):
  mid_ang, tip_rad = pp0
  seg_color = STICKCOLOR[:]
  for r in range(tip_rad, 1, -SEGMENTLEN):
    seg_color[0] = max(0, seg_color[0] - 4)
    segment_color = tuple(seg_color)
    draw_segment(dr, (mid_ang,r), tuple(seg_color))
    seg_color[2] = max(0, seg_color[2] - light_step)

def draw_sticks(dr):
  for s in range(STICKS):
    mid_ang = random.random() * tau
    rad = random.randint(1, RADIUS)
    draw_stick(dr, (mid_ang,rad))
  pass


############################## draw ####################################
img = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(img)
draw_sticks(dr)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')