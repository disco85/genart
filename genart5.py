from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
from math import *

OUT = 'genart5.png'
IMGBG = (0, 0, 0)
SIZE = (1200, 840)
CUBELONGDIAG = 120
CUBESHORTDIAG = 60
CUBEHEIGHT = 65
LINEWIDTH = 1
LINECOLOR = 'black'
CUBELEFTFACECOLOR = [200, 75, 25]  # HSL
CUBETOPFACECOLOR = [223, 75, 50]  # HSL
CUBERIGHTFACECOLOR = [223, 75, 35]  # HSL
RANDOMCOLOR = True

assert CUBESHORTDIAG < CUBELONGDIAG, 'Short diagonal must be really shorter'

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

def aspt(pt, *, x=None, y=None, rx=None, ry=None):
  l = list(pt)
  if x is not None: l[0] = x
  elif rx is not None: l[0] += rx
  if y is not None: l[1] = y
  elif ry is not None: l[1] += ry
  return tuple(l)

def is_cube_outside_horizontally(ps):
  return all(not (0 < p[0] < SIZE[0]) for p in ps)
def is_cube_outside_vertically(ps):
  return all(not (0 < p[1] < SIZE[1]) for p in ps)

def cube_points(p0):
  r'''p0 is the bottom point of the cube.
         .   <- p3
        /|\
  p2-> /_|_\ <-p4   p5,p3: short diagonal, p2,p4: long diagonal
       \ | /
       |\|/| <-p5
       | | |
  p1-> | | | <-p6   p0,p5: height
       \ | /
        \|/
         '   <-p0
  '''
  p5 = aspt(p0, ry=-CUBEHEIGHT)
  p3 = aspt(p5, ry=-CUBESHORTDIAG)
  p2 = aspt(p5, rx=-CUBELONGDIAG//2, ry=-CUBESHORTDIAG//2)
  p4 = aspt(p2, rx=CUBELONGDIAG)
  p1 = aspt(p2, ry=CUBEHEIGHT)
  p6 = aspt(p4, ry=CUBEHEIGHT)
  return [p0, p1, p2, p3, p4, p5, p6]

def draw_cube(dr, p0):
  p = cube_points(p0)
  lfc = CUBELEFTFACECOLOR[:]
  tfc = CUBETOPFACECOLOR[:]
  rfc = CUBERIGHTFACECOLOR[:]
  if RANDOMCOLOR:
    rndc = random.randint(20, 355)
    lfc[0] = tfc[0] = rfc[0] = rndc
  lfc = 'hsl(%d,%d%%,%d%%)' % tuple(lfc)
  tfc = 'hsl(%d,%d%%,%d%%)' % tuple(tfc)
  rfc = 'hsl(%d,%d%%,%d%%)' % tuple(rfc)
  dr.polygon([p[0],p[1],p[2],p[5],p[0]], fill=lfc,
             outline=LINECOLOR, width=LINEWIDTH)
  dr.polygon([p[5],p[2],p[3],p[4],p[5]], fill=tfc,
             outline=LINECOLOR, width=LINEWIDTH)
  dr.polygon([p[0],p[5],p[4],p[6],p[0]], fill=rfc,
             outline=LINECOLOR, width=LINEWIDTH)

def draw_cubes(dr, c0p0):
  start_x = c0p0[0]
  p0lt = aspt(c0p0) # left top p0
  p0rt = aspt(c0p0) # right top p0
  p0lb = aspt(c0p0) # left bottom p0
  p0rb = aspt(c0p0) # right bottom p0
  vstep = CUBEHEIGHT + (CUBESHORTDIAG//2)
  hstep = CUBELONGDIAG//2

  end = False
  flip_sign = 1
  while True:
    while True:
      plt = cube_points(p0lt)
      prt = cube_points(p0rt)
      plb = cube_points(p0lb)
      #prb = cube_points(p0rb) - unused due to the next explanation:
      # `and` in conditions bcs the canvas is not square and we can achieve
      # a border sides not at the same time. So, until both sides finish,
      # one of them will growth outside the corder.
      if (is_cube_outside_vertically(plt) and
          is_cube_outside_vertically(plb)): # prt,prb are symmetric
        end = True
        break
      elif (is_cube_outside_horizontally(plt) and
            is_cube_outside_horizontally(prt)): # plb,prb are symmetric
        break
      else:
        draw_cube(dr, p0lt)
        draw_cube(dr, p0rt)
        draw_cube(dr, p0lb)
        draw_cube(dr, p0rb)
        p0lt = aspt(p0lt, rx=-CUBELONGDIAG)
        p0rt = aspt(p0rt, rx=CUBELONGDIAG)
        p0lb = aspt(p0lb, rx=-CUBELONGDIAG)
        p0rb = aspt(p0rb, rx=CUBELONGDIAG)
    if end:
      break
    else:
      start_x += (hstep * flip_sign)
      p0lt = aspt(p0lt, x=start_x, ry=-vstep)
      p0rt = aspt(p0rt, x=start_x, ry=-vstep)
      p0lb = aspt(p0lb, x=start_x, ry=vstep)
      p0rb = aspt(p0rb, x=start_x, ry=vstep)
      flip_sign *= (-1)


############################## draw ####################################
img = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(img)
center_x = SIZE[0] // 2
center_y = SIZE[1] // 2
center = (center_x, center_y)
draw_cubes(dr, center)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')