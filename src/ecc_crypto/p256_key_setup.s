; ==============================================================================
;  file    ecc_crypto/p256_key_setup.s
;  author  vit.masek@tropicsquare.com
;
;  Copyright © 2023 Tropic Square s.r.o. (https://tropicsquare.com/)
;  This work is subject to the license terms of the LICENSE.txt file in the root
;  directory of this source tree.
;  If a copy of the LICENSE file was not distributed with this work, you can 
;  obtain one at (https://tropicsquare.com/license).
; ==============================================================================
;
; Key setup for curve NIST P-156 (ECDSA)
;
; Algorithm:
;   1) d = k mod q, if d == 0: fail
;   2) w = TMAC(d, "", 0xA)
;   3) A = d.G
;
; Input:
;   input src in r0
;   generate / store command in r1
;   physical priv key slot in r25
;   physical pub key slot in r26
;
; Outputs:
;   Writes the key set (d, w, A) to ECC key slot via KBUS
;   spect status in r3
;
; Masking methods:
;   1) Random Projective Coordinates -- (x, y, z) == (rx, ry, rz)
;   2) Group Scalar Randomization -- k' = k + r * #E
;
; See doc/ecc_key_layout.md for placement of the key values into physical slots.
;
; ==============================================================================

p256_key_setup:
    LD      r31, ca_q256

    CMPI    r1, ecc_key_gen_id
    BRZ     p256_key_setup_generate_k
    ADDI    r4,  r0,  ecc_key_store_input_k
    LDR     r19, r4
    SWE     r19, r19
    MOVI    r20,  0
    REDP    r28, r20, r19

    XOR     r1,  r28, r19
    BRNZ    p256_key_setup_fail
    XORI    r1,  r28, 0
    BRZ     p256_key_setup_fail
    JMP     p256_key_setup_start

p256_key_setup_generate_k:
    GRV     r19
    GRV     r20
    REDP    r28, r20, r19

    XORI    r1,  r28, 0
    BRZ     p256_key_setup_fail

; ==============================================================================
;   Compute w = TMAC(d, "", 0xA)
; ==============================================================================
p256_key_setup_start:
    GRV     r0
    GRV     r1
    GRV     r2
    GRV     r3

    TMAC_IT r0
    SWE     r20, r28
    TMAC_IS r20, tmac_dst_ecdsa_key_setup

    MOVI    r2,  0x04
    MOVI    r30, 17

    ; TMAC padding of an empty string
p256_key_setup_tmac_padding_loop:
    ROL8    r2,  r2
    SUBI    r30, r30, 1
    BRNZ    p256_key_setup_tmac_padding_loop
    ORI     r2, r2, 0x80

    TMAC_UP r2
    TMAC_RD r29

    ST      r28, ca_p256_key_setup_internal_d
    ST      r29, ca_p256_key_setup_internal_w

; ==============================================================================
;   Compute A = d.G
; ==============================================================================

    LD      r31, ca_q256
    GRV     r30
    SCB     r28, r28, r30

    LD      r31, ca_p256

    LD      r12, ca_p256_xG
    LD      r13, ca_p256_yG

    MOVI    r14, 1

    GRV     r14
    MOVI    r0,  0
    REDP    r14, r14, r0
    ORI     r14, r14, 1         ; Ensure that Z != 0
    MUL256  r12, r12, r14
    MUL256  r13, r13, r14

    MOV     r9,  r12
    MOV     r10, r13
    MOV     r11, r14

    CALL    point_check_p256
    BRNZ    p256_key_setup_spm_fail


    LD      r8,  ca_p256_b

    CALL    spm_p256_long
    CALL    point_check_p256
    BRNZ    p256_key_setup_spm_fail

    MOV     r1, r11
    CALL    inv_p256
    MUL256  r9, r9, r1
    MUL256  r10, r10, r1

; ==============================================================================
;   Write the keys to the slot
; ==============================================================================

    ; Compose kpair metadata (origin, curve)
    LD      r0,  ca_spect_cfg_word
    MOVI    r4,  0xFF
    AND     r20, r0,  r4                        ; mask SPECT_OP_ID to r20[7:0]
    CMPI    r20, ecc_key_gen_l3_cmd_id
    BRZ     p256_key_setup_origin_gen
p256_key_setup_origin_st:
    MOVI    r20, ecc_key_origin_st
    JMP     p256_key_setup_origin_continue
p256_key_setup_origin_gen:
    MOVI    r20, ecc_key_origin_gen

p256_key_setup_origin_continue:
    ROL8    r20, r20
    ORI     r20, r20, ecc_type_p256
    STK     r20, r26, ecc_key_metadata          ; store metadata
    BRE     p256_key_setup_fail

    ; Store the pubkey to the slot
    STK     r9,  r26, ecc_pub_key_Ax            ; store Ax
    BRE     p256_key_setup_fail
    STK     r10, r26, ecc_pub_key_Ay            ; store Ay
    BRE     p256_key_setup_fail
    KBO     r26, ecc_kbus_program               ; program
    BRE     p256_key_setup_fail
    KBO     r26, ecc_kbus_flush                 ; flush
    BRE     p256_key_setup_fail

    ; Store s and prefix to the slot
    LD      r28, ca_p256_key_setup_internal_d
    LD      r29, ca_p256_key_setup_internal_w

    MOV     r26, r25

    STK     r28, r26, ecc_priv_key_1            ; store d
    BRE     p256_key_setup_fail
    STK     r29, r26, ecc_priv_key_2            ; store w
    BRE     p256_key_setup_fail
    KBO     r26, ecc_kbus_program               ; program
    BRE     p256_key_setup_fail
    KBO     r26, ecc_kbus_flush                 ; flush
    BRE     p256_key_setup_fail

    MOVI    r3, ret_op_success

    RET
    
p256_key_setup_fail:
    KBO     r26, ecc_kbus_flush
    MOVI    r3,  ret_key_err
    RET

p256_key_setup_spm_fail:
    KBO     r26, ecc_kbus_flush
    MOVI    r3,  ret_point_integrity_err
    RET