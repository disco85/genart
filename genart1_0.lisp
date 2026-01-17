#!/usr/bin/env ros
(ros:quicklisp)
(ql:quickload "asdf")
(ql:quickload "png")


(defparameter *width* 1024)
(defparameter *height* 768)
(defparameter *sqside* 10)
(defparameter *decimation* 3)
(defparameter *sqcoord-tolerance* 5)
(defparameter *width-tolerance* 2)
(defparameter *layerdist* 5)

(defun rnd (x &optional (tol 0))
  (if (= tol 0)
      x
      (+ x (- (random (+ (* 2 tol) 1)) tol))))

(defun square-coord (col row sqside)
  (list (list (* col sqside) (* row sqside))
        (list (* (1+ col) sqside) (* (1+ row) sqside))))

(defun clamp-byte (x)
  (max 0 (min 255 x)))

(defun clamp (x lo hi)
  (max lo (min hi x)))

(defun hsl-to-rgb (h s l)
  "Convert HSL (degrees, %, %) to RGB list of 0–255 integers."
  (let* ((h (/ h 360.0))
         (s (/ s 100.0))
         (l (/ l 100.0))
         (q (if (< l 0.5) (* l (+ 1 s)) (+ l s (- (* l s)))))
         (p (- (* 2 l) q)))
    (flet ((hue-to-rgb (p q tt)
             (cond ((< tt 0) (setf tt (+ tt 1)))
                   ((> tt 1) (setf tt (- tt 1))))
             (cond ((< tt (/ 1.0 6.0)) (+ p (* (- q p) 6 tt)))
                   ((< tt 0.5) q)
                   ((< tt (/ 2.0 3.0)) (+ p (* (- q p) (- (/ 2.0 3.0) tt) 6)))
                   (t p))))
      (mapcar #'clamp-byte
              (list (round (* 255 (hue-to-rgb p q (+ h (/ 1.0 3.0)))))
                    (round (* 255 (hue-to-rgb p q h)))
                    (round (* 255 (hue-to-rgb p q (- h (/ 1.0 3.0))))))))))

(defstruct layer i sqside cols rows pencolor brushcolor)

(defun make-layer-obj (i)
  (let* ((sqside (+ 10 (* 4 i)))
         (max-col (floor (/ *width* sqside)))
         (max-row (floor (/ *height* sqside)))
         (cols (loop for c from (+ 1 (* i *layerdist*))
                     below (max 1 (- max-col 1 (* i *layerdist*)))
                     collect c))
         (rows (loop for r from (+ 1 (* i *layerdist*))
                     below (max 1 (- max-row 1 (* i *layerdist*)))
                     collect r))
         (pencolor (list (* 50 i) (+ 10 (* 10 (- 3 i))) (+ 4 (* 6 i))))
         (brushcolor (list (+ 24 (* i 10)) (* 10 (- 3 i)) (+ 25 (* 10 i)))))
    (make-layer :i i :sqside sqside :cols (or cols '(0)) :rows (or rows '(0))
                :pencolor pencolor :brushcolor brushcolor)))

(defun randomize-color (hsl s-tol l-tol)
  (destructuring-bind (h s l) hsl
    (list h (rnd s s-tol) (rnd l l-tol))))

(defun clip-rect (x1 y1 x2 y2)
  "Clip rectangle to image bounds and return (nx1 ny1 nx2 ny2) or NIL if empty."
  (let* ((nx1 (clamp (min x1 x2) 0 (1- *width*)))
         (ny1 (clamp (min y1 y2) 0 (1- *height*)))
         (nx2 (clamp (max x1 x2) 0 (1- *width*)))
         (ny2 (clamp (max y1 y2) 0 (1- *height*))))
    (if (or (> nx1 nx2) (> ny1 ny2))
        nil
        (list nx1 ny1 nx2 ny2))))

(defun draw-square (pixels coords fill outline)
  (destructuring-bind ((x1 y1) (x2 y2)) coords
    (let ((rect (clip-rect x1 y1 x2 y2)))
      (when rect
        (destructuring-bind (cx1 cy1 cx2 cy2) rect
          (let ((w (1+ (- cx2 cx1)))
                (h (1+ (- cy2 cy1))))
            ;; fill
            (destructuring-bind (fr fg fb) (hsl-to-rgb (first fill) (second fill) (third fill))
              (dotimes (yy h)
                (dotimes (xx w)
                  (let ((x (+ cx1 xx)) (y (+ cy1 yy)))
                    (setf (aref pixels y x 0) fr)
                    (setf (aref pixels y x 1) fg)
                    (setf (aref pixels y x 2) fb)))))
            ;; outline (top/bottom)
            (destructuring-bind (or og ob) (hsl-to-rgb (first outline) (second outline) (third outline))
              (dotimes (xx w)
                (let ((x (+ cx1 xx)))
                  (setf (aref pixels cy1 x 0) or)
                  (setf (aref pixels cy1 x 1) og)
                  (setf (aref pixels cy1 x 2) ob)
                  (setf (aref pixels cy2 x 0) or)
                  (setf (aref pixels cy2 x 1) og)
                  (setf (aref pixels cy2 x 2) ob)))
              ;; outline (left/right)
              (dotimes (yy h)
                (let ((y (+ cy1 yy)))
                  (setf (aref pixels y cx1 0) or)
                  (setf (aref pixels y cx1 1) og)
                  (setf (aref pixels y cx1 2) ob)
                  (setf (aref pixels y cx2 0) or)
                  (setf (aref pixels y cx2 1) og)
                  (setf (aref pixels y cx2 2) ob))))))))))

(defun draw-layer (pixels layer)
  (dolist (col (layer-cols layer))
    (dolist (row (layer-rows layer))
      (when (= 0 (mod (random 21) *decimation*))
        (let* ((coords (mapcar (lambda (xy)
                                 (list (rnd (first xy) *sqcoord-tolerance*)
                                       (rnd (second xy) *sqcoord-tolerance*)))
                               (square-coord col row (layer-sqside layer))))
               (outline (randomize-color (layer-pencolor layer) 10 30))
               (fill (randomize-color (layer-brushcolor layer) 70 10)))
          (draw-square pixels coords fill outline))))))

(defun main ()
  ;; 3D array: height × width × 3 channels
  (let ((pixels (make-array (list *height* *width* 3)
                            :element-type '(unsigned-byte 8)
                            :initial-element 0)))
    ;; background
    (dotimes (y *height*)
      (dotimes (x *width*)
        (setf (aref pixels y x 0) 40)
        (setf (aref pixels y x 1) 20)
        (setf (aref pixels y x 2) 2)))
    ;; layers
    (dotimes (i 3)
      (draw-layer pixels (make-layer-obj i)))
    ;; save PNG
    (with-open-file (out "genart1.png"
                     :direction :output
                     :element-type '(unsigned-byte 8)
                     :if-exists :supersede
                     :if-does-not-exist :create)
      (png:encode pixels out))))

(main)
(format t "Generated genart1.png~%")
