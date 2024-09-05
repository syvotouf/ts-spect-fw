; ==============================================================================
;  file    ecc_math/p256/point_dbl_p256.s
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
; Point Doubling on curve P-256
; Uses Algorithm 6 from https://eprint.iacr.org/2015/1060.pdf
; Input:
;   Point Q0 = (r9, r10, r11)
;
; Output:
;   Point Q0 = 2 Q0
;
; Expects:
;   p256 prime in r31
;   P-256 parameter b in r8
;
; Intermediate value registers:
;   r0-7
;
; ==============================================================================

point_dbl_p256:
    MUL256  r0,  r9,  r9
    MUL256  r1,  r10, r10
    MUL256  r2,  r11, r11
    MUL256  r3,  r9,  r10
    ADDP    r3,  r3,  r3
    MUL256  r7,  r9,  r11
    ADDP    r7,  r7,  r7
    MUL256  r6,  r8,  r2
    SUBP    r6,  r6,  r7
    ADDP    r5,  r6,  r6
    ADDP    r6,  r5,  r6
    SUBP    r5,  r1,  r6
    ADDP    r6,  r1,  r6
    MUL256  r6,  r5,  r6
    MUL256  r5,  r5,  r3
    ADDP    r3,  r2,  r2
    ADDP    r2,  r2,  r3
    MUL256  r7,  r8,  r7
    SUBP    r7,  r7,  r2
    SUBP    r7,  r7,  r0
    ADDP    r3,  r7,  r7
    ADDP    r7,  r7,  r3
    ADDP    r3,  r0,  r0
    ADDP    r0,  r3,  r0
    SUBP    r0,  r0,  r2
    MUL256  r0,  r0,  r7
    ADDP    r6,  r6,  r0
    MUL256  r0,  r10, r11
    ADDP    r0,  r0,  r0
    MUL256  r7,  r0,  r7
    SUBP    r5,  r5,  r7
    MUL256  r7,  r0,  r1
    ADDP    r7,  r7,  r7
    ADDP    r7,  r7,  r7
    MOV     r9,  r5
    MOV     r10, r6
    MOV     r11, r7
    RET
