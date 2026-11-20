;; Loading defines helpers only. Call cadmac:run explicitly from an idle prompt.

(defun cadmac:context ()
  (mapcar 'getvar '("DWGPREFIX" "DWGNAME" "CTAB" "TILEMODE" "CVPORT")))

(defun cadmac:group-active-p ()
  (/= 0 (logand 8 (getvar "UNDOCTL"))))

(defun cadmac:restore (expected saved close-group / item result issues)
  (if (not (equal expected (cadmac:context)))
    '(CONTEXT_CHANGED)
    (progn
      (foreach item saved
        (if (not (equal (getvar (car item)) (cdr item)))
          (progn
            (setq result (vl-catch-all-apply 'setvar (list (car item) (cdr item))))
            (if (or (vl-catch-all-error-p result)
                    (not (equal (getvar (car item)) (cdr item))))
              (setq issues (cons (car item) issues))))))
      (if (and close-group (cadmac:group-active-p))
        (progn
          (setq result (vl-catch-all-apply 'command-s '("_.UNDO" "_End")))
          (if (or (vl-catch-all-error-p result) (cadmac:group-active-p))
            (setq issues (cons "UNDO" issues)))))
      (reverse issues))))

(defun cadmac:run (expected task overrides / *error* saved own-group undoctl result issues)
  ;; Task returns a non-nil receipt. Keep work in this document and viewport.
  (defun *error* (message)
    (prin1 (list 'CADMAC-ABORTED message (cadmac:restore expected saved own-group)))
    (princ))
  (setq undoctl (getvar "UNDOCTL"))
  (cond
    ((not (equal expected (cadmac:context))) '(CADMAC-REFUSED CONTEXT))
    ((/= 0 (logand 95 (getvar "CMDACTIVE"))) '(CADMAC-REFUSED BUSY))
    ((or (= 0 (logand 1 undoctl)) (/= 0 (logand 10 undoctl)))
     '(CADMAC-REFUSED UNDO-STATE))
    (T
     (setq saved (mapcar '(lambda (pair) (cons (car pair) (getvar (car pair)))) overrides))
     (setq own-group T)
     (setq result
       (vl-catch-all-apply
         '(lambda (/ pair)
            (command-s "_.UNDO" "_Begin")
            (if (cadmac:group-active-p)
              (progn
                (foreach pair overrides (setvar (car pair) (cdr pair)))
                (apply task nil))))
         nil))
     (setq issues (cadmac:restore expected saved own-group)
           own-group nil
           saved nil)
     (cond
       (issues (list 'CADMAC-CLEANUP-FAILED issues))
       ((vl-catch-all-error-p result) (list 'CADMAC-FAILED (vl-catch-all-error-message result)))
       (result (list 'CADMAC-OK result))
       (T '(CADMAC-FAILED NO-RECEIPT))))))

(princ "\nCADMAC helpers loaded.")
(princ)
