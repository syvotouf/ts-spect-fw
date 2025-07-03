; ==============================================================================
;  file    ecc_math/p256/spm_p256_short.s 
;  author  vit.masek@tropicsquare.com
;
;  Copyright © 2023 Tropic Square s.r.o. (https://tropicsquare.com/)
;  This work is subject to the license terms of the LICENSE.txt file in the root
;  directory of this source tree.
;  If a copy of the LICENSE file was not distributed with this work, you can 
;  obtain one at (https://tropicsquare.com/license).
;
; ==============================================================================
;
; Scalar Point Multiplication on curve P-256
; Uses CSWAP Montgomery Ladder method [https://eprint.iacr.org/2017/293]
;
; Inputs:
;   Point P = (r12, r13, r14)
;   Scalar k = (r28)
;
; Output:
;   Point Q = (r9,r10,r11)
;
; Expects:
;   p256 prime in r31
;   P-256 parameter b in r8
;       (b = 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b)
;
; Intermediate value registers:
;   r0-r7 -> intermediate values for point addition/doubling
;   r8 -> parameter b
;   (r9, r10, r11) -> Q0
;   r30 -> counter
;
; =============================================================================

spm_p256_short:
    ; (r9, r10, r11) = Q0 = "point at infinity O"
    MOVI    r9,  0
    MOVI    r10, 1
    MOVI    r11, 0

    MOVI    r30, 256

    MOVI    r30, 256
spm_p256_short_loop:
    ROL     r28, r28

    CSWAP   r9,  r12
    CSWAP   r10, r13
    CSWAP   r11, r14

    CALL    point_add_p256
    CALL    point_dbl_p256

    CSWAP   r9,  r12
    CSWAP   r10, r13
    CSWAP   r11, r14

    SUBI    r30, r30, 1
    BRNZ    spm_p256_short_loop

    RET
