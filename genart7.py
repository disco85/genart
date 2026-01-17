from PIL import Image, ImageDraw, ImageFont, ImageColor
import random
import itertools
import math


OUT = 'genart7.png'
IMGBG = (20, 40, 50)
SIZE = (1200, 900)
AVERAGECELL = 400
CELLSIZETOLERANCE = 30
CELLS = 80 # number of cells
LAYERS = 4  # number of layers
NOISELEVEL = 3
SHADOWOFFSET = (5, 5)
SHADOWSTEP = .05  # per pixel
GLOBALSHADOWSTEP = 0.02
SHADOWDEPTH = 33  # decrement to get shadow
# base HSV-colors
COLORS = [[203,0,90], [203,63,60], [263,1,37]]
LINECOLOR = '#050505'


Center = (SIZE[0] // 2, SIZE[1] // 2)
NoPxl, DarkPxl = 0, 1
Lighting = [[NoPxl for y in range(SIZE[1])] for x in range(SIZE[0])] # Shadows

def rnd(x, tolerance=None, step=None):
  if not tolerance:
    return x
  else:
    return random.randrange(x - tolerance, x + tolerance, step or 1)

def to_axis(pt):
  return (pt[0] - (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def from_axis(pt):
  return (pt[0] + (SIZE[0]//2), (SIZE[1]//2) - pt[1])

def is_segment_point(seg, x):
  x1, x2 = seg
  if x1 <= x <= x2: return True
  elif x2 <= x <= x1: return True
  else: return False

def distance(pt1, pt2):
  return int(math.sqrt(((pt2[0] - pt1[0])**2) + ((pt2[1] - pt1[1])**2)))

def determine_line(p1, p2):
  'Determines the equation on 2 points'
  x1,y1 = p1; x2,y2 = p2
  if x1 != x2:
    k = (y1 - y2) / (x1 - x2)
    b = y2 - k*x2
    return dict(k=k, b=b, domain=(x1,x2), codomain=(y1,y2))
  else:
    return dict(k=math.inf, b=None, domain=(x1,x2), codomain=(y1,y2))

def line_y(line, x):
  '''Take line as a dict, see `determine_line()` and `x` and returns line's `[y]`
  which length is one or more (when line is vertical) or zero (when line is
  vertical and `x` is out of domain)
  '''
  if line['k'] == math.inf:
    if is_segment_point(line['domain'], x):
      y0, y1 = sorted(line['codomain'])
      return list(range(y0, y1+1))
    else: return []
  else:
    if is_segment_point(line['domain'], x):
      return [int(line['k']*x + line['b'])]
    else: return []

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

def cell_segments(cell):
  'All segments of cell consisting of 3, 4 points'
  is_horiz_seg = lambda p1,p2: p1[1] == p2[1]
  is_vert_seg = lambda p1,p2: p1[0] == p2[0]
  cell_len = len(cell)
  assert 0 < cell_len < 5, 'Unsupported cell of %d points' % cell_len
  opts = list(itertools.combinations(cell, 2))
  if cell_len == 3: return opts
  elif cell_len == 4:
    opts = [seg for seg in opts if is_horiz_seg(*seg) or is_vert_seg(*seg)]
    return opts

def generate_cells():
  '''Generates cells as a list of points lists (point-tuple `(x,y)`).
  Points-list can have 3 or 4 elements.'''
  cells = []
  layer_cells = CELLS // LAYERS
  aver_cell = AVERAGECELL
  for i in range(CELLS):
    layer = 1 + (i // layer_cells)
    mid_x = random.randint(1, SIZE[0] - 1)
    mid_y = random.randint(1, SIZE[1] - 1)
    w = rnd(aver_cell//layer, CELLSIZETOLERANCE, step=5)
    h = rnd(aver_cell//layer, CELLSIZETOLERANCE, step=5)
    lt = (0, mid_x - w//2, mid_y - h//2)
    rt = (1, mid_x + w//2, mid_y - h//2)
    rb = (2, mid_x + w//2, mid_y + h//2)
    lb = (3, mid_x - w//2, mid_y + h//2)
    opts = [lt, rt, rb, lb]
    pts = []
    for ntries in range(random.choice((3,4))):  # triangles or rectangles
      pt = random.choice(opts)
      pts.append(pt)
      opts.remove(pt)
    cells.append([p[1:] for p in sorted(pts, key=lambda p: p[0])])
  return cells

#def debug1(dr, cells, color=[100,200,300]):
#  for cell in cells:
#    if color:
#      color[0] = random.randint(20,255)
#      color[1] = random.randint(20,255)
#      dr.polygon([p for p in cell], fill=tuple(color))
#    else:
#      dr.polygon([p for p in cell])

def draw_vert_line(dr_or_light, x, y0, y1, *, line_num=0, del_shadow=False,
                   base_color='white'):
  if not (0 < x < SIZE[0]):
    return
  y0 = max(0, min(SIZE[1] - 1, y0))
  y1 = max(0, min(SIZE[1] - 1, y1))
  if y0 > y1:
    y0, y1 = y1, y0
  if dr_or_light is Lighting:
    for y in range(y0, y1 + 1):
      Lighting[x][y] = int(not del_shadow)
  else:
    for y in range(y0, y1 + 1):
      color = vert_gradient_point(base_color, x, y, y0, noise=True,
                                  global_gradient=True)
      color = 'hsv(%d,%d%%,%d%%)' % color
      dr.point((x,y), fill=color)

def vert_gradient_point(base_color, x, y, y0, *, noise=True,
                        global_gradient=False):
  '''Returns HSV-color from `base_color` (HSV too), generating noise and adding
  global gradient'''
  color = list(base_color)
  if noise:
    color[1] = rnd(color[1], NOISELEVEL)
    color[2] = rnd(color[2], NOISELEVEL)
  local_y_dist = y - y0
  global_y_dist = y
  color[2] -= ((local_y_dist * SHADOWSTEP) +
               ((global_y_dist * GLOBALSHADOWSTEP) if global_gradient else 0))
  color[1] = max(0, min(100, color[1]))
  color[2] = max(0, min(100, color[2]))
  return tuple(color)

def find_top_line(segs):
  'Finds top horizontal line of the cell segments (axis coord are used)'
  top_y = max((p for seg in segs for p in seg), key=lambda p: p[1])[1]
  horiz = [seg for seg in segs if seg[0][1] == seg[1][1] and seg[0][1] == top_y]
  return horiz[0] if horiz else None

def draw_cells(dr, cells):
  # Due to different algorithms of line drawing (I paint solid cells face by
  # vertical lines that forms sides of triangles too, but PIL draws sides -
  # the outline in a different way, so I get solid face outside outline by
  # 1-2 pixels, so I do this fix for 0x, 0y with +/- fix_outline pixel):
  fix_outline = 2
  for cnv_cell in cells:  # cnv_cell: canvas coord cells
    base_color = list(random.choice(COLORS))
    cell = [to_axis(p) for p in cnv_cell]
    bbox = bound_box(cell)
    segs = cell_segments(cell)
    lines = [determine_line(*seg) for seg in segs]
    xrng = sorted([bbox[0][0], bbox[1][0] + 1])
    xrng[0] += fix_outline
    xrng[1] -= fix_outline
    for line_num, x in enumerate(range(*xrng)):
      ys = sum((line_y(line, x) for line in lines), [])  # flatten
      if ys:
        y0 = min(ys)
        y1 = max(ys)
        ps = [from_axis(p) for p in [(x,y0), (x,y1)]]
        shad_ps = [(p[0] + SHADOWOFFSET[0], p[1] + SHADOWOFFSET[1]) for p in ps]
        draw_vert_line(dr, ps[0][0], # 0x is the same (cos vertical)
                       # y0 is min, y1 is max so why min-fix, max+fix and not
                       # min+fix, max-fix? BCS min,max are on axis, not on
                       # canvas! On canvas they are swapped:
                       ps[0][1] - fix_outline, ps[1][1] + fix_outline,
                       line_num=line_num, base_color=base_color)
        draw_vert_line(Lighting, shad_ps[0][0], shad_ps[0][1], shad_ps[1][1])
        draw_vert_line(Lighting, ps[0][0], ps[0][1], ps[1][1], del_shadow=True)
    top_line = find_top_line(segs)
    if top_line:
      color = base_color[:]
      color[2] += 7  # light top line
      color[2] = min(100, color[2])
      color = 'hsv(%d,%d%%,%d%%)' % tuple(color)
      top_line = ((p[0] + 5 if i==0 else p[0] - 5, p[1] - 3)
                  for i, p in enumerate(top_line))
      top_pts = [from_axis(p) for p in top_line]
      dr.line(top_pts, fill=color, width=2)
    dr.polygon(cnv_cell, outline=LINECOLOR, width=2)

def draw_lighting(img):
  for y in range(SIZE[1]):
    for x in range(SIZE[0]):
      if Lighting[x][y] == DarkPxl:
        rgb = img.getpixel((x,y))
        rgb = (rgb[0] - SHADOWDEPTH, rgb[1] - SHADOWDEPTH, rgb[2] - SHADOWDEPTH)
        img.putpixel((x,y), rgb)


############################## draw ####################################
img = Image.new("RGB", SIZE, IMGBG)
dr = ImageDraw.Draw(img)
cells = generate_cells()
draw_cells(dr, cells)
draw_lighting(img)

with open(OUT, 'wb') as f:
  img.save(f, format='PNG')