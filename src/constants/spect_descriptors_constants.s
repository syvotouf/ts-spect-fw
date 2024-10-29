; ==============================================================================
;  file    constants/spect_descriptors_constants.s
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
;   Descriptor constants
;   - config and result word address
;   - ECC type values
;   - KBUS descriptors
;   - TMAC domain separation tag
;
; ==============================================================================

; config and result word address
ca_spect_cfg_word .eq 0x0100
ca_spect_res_word .eq 0x1100

; ECC type values
ecc_type_ed25519 .eq 0x02
ecc_type_p256 .eq 0x01

; ECC key origins values
ecc_key_gen_l3_cmd_id .eq 0x60
ecc_key_st_l3_cmd_id .eq 0x61
ecc_key_origin_gen .eq 0x01
ecc_key_origin_st .eq 0x02

; ECC additional metadata values
ecc_priv_slot_id .eq 0x55
ecc_pub_slot_id .eq 0xAA


; KBUS descriptors
ecc_priv_key_1 .eq 0x400
ecc_priv_key_2 .eq 0x401
ecc_priv_key_3 .eq 0x402
ecc_priv_key_4 .eq 0x403
ecc_key_metadata .eq 0x404
ecc_pub_key_Ax .eq 0x405
ecc_pub_key_Ay .eq 0x406
ecc_kbus_program .eq 0x402
ecc_kbus_flush .eq 0x405
ecc_kbus_erase .eq 0x403
ecc_kbus_verify_erase .eq 0x404

; TMAC DSTs
tmac_dst_ecdsa_key_setup .eq 0xA
tmac_dst_ecdsa_sign .eq 0xB
tmac_dst_eddsa_sign .eq 0xC

; GF(p) gen DSTs
gfp_gen_dst_ecdsa .eq 0xF1
gfp_gen_dst_eddsa .eq 0xF2
gfp_gen_dst_x25519 .eq 0xF3
gfp_gen_dst_ecc_key .eq 0xF4
