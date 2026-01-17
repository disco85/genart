#!/usr/bin/env scala

import java.awt.image.BufferedImage
import java.awt.{Color, Graphics2D, RenderingHints}
import java.awt.geom.Rectangle2D
import javax.imageio.ImageIO
import scala.util.Random

val random = Random()  // for reproducibility can be `Random(1234)`

val IMGBG_RGB = (40, 20, 2)
val SIZE = (1024, 768)
val SQSIDE = 10
val DECIMATION = 3 // skip every N square
val SQCOORDTOLERANCE = 5
val WIDTHTOLERANCE = 2
val PENCOLOR_HSL = (90, 64, 20) // (Hue, Saturation%, Lightness%)
val BRUSHCOLOR_HSL = (54, 27, 21)
val LAYERDIST = 5 // distance between layers in squares


def rnd(x: Int, tolerance: Int = 0, positive: Boolean = true): Int =
  val res = if tolerance == 0 then x else random.between(x - tolerance, x + tolerance + 1) // +1 for inclusive range
  if positive then Math.abs(res) else res

def squareCoord(col: Int, row: Int, sqside: Int = SQSIDE): List[(Int, Int)] =
  List((col * sqside, row * sqside), ((col + 1) * sqside, (row + 1) * sqside))

/**
 * Converts an HSL color to an AWT Color object.
 * HSL is defined as (Hue in 0-360, Saturation in 0-100, Lightness in 0-100).
 */
def hslToRgb(h: Int, s: Int, l: Int): Color =
  val hNorm = h / 360.0
  val sNorm = s / 100.0
  val lNorm = l / 100.0

  val q = if lNorm < 0.5 then lNorm * (1.0 + sNorm) else lNorm + sNorm - lNorm * sNorm
  val p = 2.0 * lNorm - q

  def hueToRgb(p: Double, q: Double, t: Double): Double =
    if t < 0 then t + 1.0
    else if t > 1 then t - 1.0
    else if t < 1.0 / 6.0 then p + (q - p) * 6.0 * t
    else if t < 0.5 then q
    else if t < 2.0 / 3.0 then p + (q - p) * (2.0 / 3.0 - t) * 6.0
    else p

  val r = (hueToRgb(p, q, hNorm + 1.0 / 3.0) * 255).toInt
  val g = (hueToRgb(p, q, hNorm) * 255).toInt
  val b = (hueToRgb(p, q, hNorm - 1.0 / 3.0) * 255).toInt
  new Color(r, g, b)



class Layer(i: Int):
  val sqside = 10 + 4 * i
  val (width, height) = SIZE
  val cols = (1 + i * LAYERDIST) until (width / sqside - 1 - i * LAYERDIST)
  val rows = (1 + i * LAYERDIST) until (height / sqside - 1 - i * LAYERDIST)

  private val _pencolor_hsl = (50 * i, 10 + 10 * (3 - i), 4 + 6 * i)
  private val _brushcolor_hsl = (24 + i * 10, 10 * (3 - i), 25 + 10 * i)

  def pencolor: (Int, Int, Int) =
    val (h, s, l) = _pencolor_hsl
    (h, rnd(s, 10), rnd(l, 30))

  def brushcolor: (Int, Int, Int) =
    val (h, s, l) = _brushcolor_hsl
    (h, rnd(s, 70), rnd(l, 10))



def drawSquare(g2d: Graphics2D, coords: List[(Int, Int)], fillColor: Color, outlineColor: Color, width: Int): Unit =
  val (x1, y1) = coords.head
  val (x2, y2) = coords(1)
  val rect = new Rectangle2D.Double(x1, y1, x2 - x1, y2 - y1)

  g2d.setColor(fillColor)
  g2d.fill(rect)

  g2d.setColor(outlineColor)
  g2d.setStroke(new java.awt.BasicStroke(width))
  g2d.draw(rect)

def drawLayer(g2d: Graphics2D, layer: Layer): Unit =
  for
    col <- layer.cols
    row <- layer.rows
  do
    // This means "if NOT divisible by DECIMATION, continue"
    if random.nextInt(21) % DECIMATION != 0 then
      val baseCoords = squareCoord(col, row, layer.sqside)
      val coords = baseCoords.map { case (x, y) => (rnd(x, SQCOORDTOLERANCE), rnd(y, SQCOORDTOLERANCE)) }

      val (h, s, l) = layer.pencolor
      val (h2, s2, l2) = layer.brushcolor

      val outlineColor = hslToRgb(h, s, l)
      val fillColor = hslToRgb(h2, s2, l2)
      val strokeWidth = rnd(1, WIDTHTOLERANCE)

      drawSquare(g2d, coords, fillColor, outlineColor, strokeWidth)



val (width, height) = SIZE
val (bgR, bgG, bgB) = IMGBG_RGB


val image = new BufferedImage(width, height, BufferedImage.TYPE_INT_RGB)
val g2d = image.createGraphics()

// Set background color
g2d.setColor(new Color(bgR, bgG, bgB))
g2d.fillRect(0, 0, width, height)

// Improve rendering quality
g2d.setRenderingHint(RenderingHints.KEY_ANTIALIASING, RenderingHints.VALUE_ANTIALIAS_ON)

// Draw each layer
for i <- 0 to 2 do
  drawLayer(g2d, Layer(i))

// Clean up the graphics context
g2d.dispose()

val outputFile = java.io.File("genart1.png")
ImageIO.write(image, "PNG", outputFile)
println(s"Successfully generated art at ${outputFile.getAbsolutePath}")
