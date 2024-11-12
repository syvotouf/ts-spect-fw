#!/usr/bin/env python3
import sys
import random as rn
import os

import test_common as tc

import models.ed25519 as ed25519

defines_set = tc.get_main_defines()

def eddsa_sequence(s, prefix, A, slot, sch, scn, message, run_name_suffix):

    insrc = 0x4
    if "IN_SRC_EN" in defines_set:
        insrc = tc.insrc_arr[rn.randint(0,1)]

    outsrc = 0x5
    if "OUT_SRC_EN" in defines_set:
        outsrc = tc.outsrc_arr[rn.randint(0,1)]

    smodq = s % ed25519.q

    sign_ref = ed25519.sign(s, prefix, A, sch, scn, message)

    ########################################################################################################
    #   Set Context
    ########################################################################################################
    run_name = "eddsa_set_context" + run_name_suffix
    tc.print_run_name(run_name)

    rng = [rn.randint(0, 2**256-1) for _ in range(10)]
    tc.set_rng(test_dir, rng)

    cmd_file = tc.get_cmd_file(test_dir)
    tc.start(cmd_file)

    if run_name_suffix != "_empty_slot":
        smask = rn.randint(0, ed25519.q-1)
        s1 = smask
        s2 = (smodq - smask) % ed25519.q

        prefix_mask = rn.randint(0, 2**256-1)
        prefix_masked = prefix ^ prefix_mask

        tc.set_key(cmd_file, key=s1,            ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k1"])
        tc.set_key(cmd_file, key=prefix_masked, ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k2"])
        tc.set_key(cmd_file, key=s2,            ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k3"])
        tc.set_key(cmd_file, key=prefix_mask,   ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k4"])

        if run_name_suffix == "_invalid_curve":
            invalid_metadata = "curve"
        else:
            invalid_metadata = None

        _, _ = tc.gen_and_set_metadata(
            curve=tc.Ed25519_ID,
            slot=slot,
            origin=0x01,
            cmd_file=cmd_file,
            invalid_metadata=invalid_metadata
        )

        A_int = int.from_bytes(A, 'big')
        tc.set_key(cmd_file, key=A_int,     ktype=0x04, slot=(slot<<1)+1, offset=tc.PUB_SLOT_LAYOUT["x"])

    input_word = (slot << 8) + tc.find_in_list("eddsa_set_context", ops_cfg)["id"]

    tc.write_int32(cmd_file, input_word, (insrc<<12))

    tc.write_bytes(cmd_file, sch, 0x00A0)
    tc.write_bytes(cmd_file, scn, 0x00C0)

    ctx = tc.run_op(cmd_file, "eddsa_set_context", insrc, outsrc, 36, ops_cfg, test_dir, run_name=run_name)

    SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

    if (run_name_suffix == "_empty_slot"):
        if (SPECT_OP_STATUS != 0xF2):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0
        if (SPECT_OP_DATA_OUT_SIZE != 1):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0
        l3_result = tc.read_output(test_dir, run_name, (outsrc<<12), 1)
        if (l3_result != 0x12):
            print("L3 RESULT:", hex(l3_result))
            return 0

        return 1
    elif (run_name_suffix == "_invalid_curve"):
        if (SPECT_OP_STATUS != 0xF4):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0
        if (SPECT_OP_DATA_OUT_SIZE != 1):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0
        l3_result = tc.read_output(test_dir, run_name, (outsrc<<12), 1)
        if (l3_result != 0x12):
            print("L3 RESULT:", hex(l3_result))
            return 0
        return 1
    else:
        if (SPECT_OP_STATUS != 0x00):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0
        if (SPECT_OP_DATA_OUT_SIZE != 0):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0

        if "ECC_KEY_RERANDOMIZE" in defines_set:
            kmem_data, _ = tc.parse_key_mem(test_dir, run_name)

            remasked_s1         = tc.get_key(kmem_data, ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k1"])
            remasked_prefix     = tc.get_key(kmem_data, ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k2"])
            remasked_s2         = tc.get_key(kmem_data, ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k3"])
            remasked_prefixmask = tc.get_key(kmem_data, ktype=0x04, slot=(slot<<1), offset=tc.PRIV_SLOT_LAYOUT["k4"])

            b1 = ((remasked_s1 + remasked_s2) % ed25519.q) == ((s1 + s2) % ed25519.q)
            b2 = (remasked_s1 != s1) and (remasked_s2 != s2)
            b3 = (remasked_prefix ^ remasked_prefixmask) == (prefix_int ^ prefixmask)
            b4 = (remasked_prefix != prefix_int) and (remasked_prefixmask != prefixmask)

            if not(b1 and b2):
                print("Remasking of s failed.")
                return 0

            if not(b3 and b4):
                print("Remasking of prefix failed.")
                return 0

    ########################################################################################################
    #   Nonce Init
    ########################################################################################################
    run_name = "eddsa_nonce_init" + run_name_suffix
    tc.print_run_name(run_name)

    rng = [rn.randint(0, 2**256-1) for i in range(10)]
    tc.set_rng(test_dir, rng)

    cmd_file = tc.get_cmd_file(test_dir)
    tc.start(cmd_file)

    ctx = tc.run_op(cmd_file, "eddsa_nonce_init", insrc, outsrc, 36, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

    SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

    if (SPECT_OP_STATUS):
        print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
        return 0

    if (SPECT_OP_DATA_OUT_SIZE != 0):
        print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
        return 0

    ########################################################################################################
    #   Nonce Update
    ########################################################################################################
    updates_cnt = len(message) // 144
    for i in range(0, updates_cnt):
        block = message[i*144:i*144+144]
        run_name = f"eddsa_nonce_update_{i}" + run_name_suffix
        tc.print_run_name(run_name)

        cmd_file = tc.get_cmd_file(test_dir)
        tc.start(cmd_file)

        tc.write_bytes(cmd_file, block, (insrc<<12))
        ctx = tc.run_op(cmd_file, "eddsa_nonce_update", insrc, outsrc, 144, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

        SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

        if (SPECT_OP_STATUS):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0

        if (SPECT_OP_DATA_OUT_SIZE != 0):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0

    ########################################################################################################
    #   Nonce Finish
    ########################################################################################################
    last_block_tmac = message[updates_cnt*144:]

    run_name = "eddsa_nonce_finish" + run_name_suffix
    tc.print_run_name(run_name)

    cmd_file = tc.get_cmd_file(test_dir)
    tc.start(cmd_file)

    tc.write_bytes(cmd_file, last_block_tmac, (insrc<<12))

    ctx = tc.run_op(cmd_file, "eddsa_nonce_finish", insrc, outsrc, len(last_block_tmac), ops_cfg, test_dir, run_name=run_name, old_context=ctx)

    SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

    if (SPECT_OP_STATUS):
        print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
        return 0

    if (SPECT_OP_DATA_OUT_SIZE != 0):
        print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
        return 0

    ########################################################################################################
    #   R Part
    ########################################################################################################
    run_name = "eddsa_R_part" + run_name_suffix
    tc.print_run_name(run_name)

    rng = [rn.randint(0, 2**256-1) for _ in range(10)]
    tc.set_rng(test_dir, rng)

    cmd_file = tc.get_cmd_file(test_dir)
    tc.start(cmd_file)

    ctx = tc.run_op(cmd_file, "eddsa_R_part", insrc, outsrc, 0, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

    SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

    if (SPECT_OP_STATUS):
        print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
        return 0

    if (SPECT_OP_DATA_OUT_SIZE != 0):
        print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
        return 0

    if len(message) < 64:
        ########################################################################################################
        #   E at once
        ########################################################################################################
        run_name = "eddsa_e_at_once" + run_name_suffix
        tc.print_run_name(run_name)

        cmd_file = tc.get_cmd_file(test_dir)
        tc.start(cmd_file)

        tc.write_bytes(cmd_file, message, (insrc<<12))

        ctx = tc.run_op(cmd_file, "eddsa_e_at_once", insrc, outsrc, len(message), ops_cfg, test_dir, run_name=run_name, old_context=ctx)

        SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

        if (SPECT_OP_STATUS):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0

        if (SPECT_OP_DATA_OUT_SIZE != 0):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0
    else:
        ########################################################################################################
        #   E Prep
        ########################################################################################################
        m_block_prep = message[:64]

        run_name = "eddsa_e_prep" + run_name_suffix
        tc.print_run_name(run_name)

        cmd_file = tc.get_cmd_file(test_dir)
        tc.start(cmd_file)

        tc.write_bytes(cmd_file, m_block_prep, (insrc<<12))

        ctx = tc.run_op(cmd_file, "eddsa_e_prep", insrc, outsrc, 64, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

        SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

        if (SPECT_OP_STATUS):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0

        if (SPECT_OP_DATA_OUT_SIZE != 0):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0

        ########################################################################################################
        #   E Update
        ########################################################################################################
        message_tmp = message[64:]
        updates_cnt = len(message_tmp) // 128

        for i in range(0, updates_cnt):
            block = message_tmp[i*128:i*128+128]
            run_name = f"eddsa_e_update_{i}" + run_name_suffix
            tc.print_run_name(run_name)

            cmd_file = tc.get_cmd_file(test_dir)
            tc.start(cmd_file)

            tc.write_bytes(cmd_file, block, (insrc<<12))
            ctx = tc.run_op(cmd_file, "eddsa_e_update", insrc, outsrc, 128, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

            SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

            if (SPECT_OP_STATUS):
                print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
                return 0

            if (SPECT_OP_DATA_OUT_SIZE != 0):
                print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
                return 0

        ########################################################################################################
        #   E Finish
        ########################################################################################################
        run_name = "eddsa_e_finish" + run_name_suffix
        tc.print_run_name(run_name)

        last_block = message_tmp[updates_cnt*128:]

        cmd_file = tc.get_cmd_file(test_dir)
        tc.start(cmd_file)

        tc.write_bytes(cmd_file, last_block, (insrc<<12))

        ctx = tc.run_op(cmd_file, "eddsa_e_finish", insrc, outsrc, len(last_block), ops_cfg, test_dir, run_name=run_name, old_context=ctx)

        SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

        if (SPECT_OP_STATUS):
            print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
            return 0

        if (SPECT_OP_DATA_OUT_SIZE != 0):
            print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
            return 0

    ########################################################################################################
    #   Finish
    ########################################################################################################
    run_name = "eddsa_finish" + run_name_suffix
    tc.print_run_name(run_name)

    cmd_file = tc.get_cmd_file(test_dir)
    tc.start(cmd_file)

    ctx = tc.run_op(cmd_file, "eddsa_finish", insrc, outsrc, 0, ops_cfg, test_dir, run_name=run_name, old_context=ctx)

    SPECT_OP_STATUS, SPECT_OP_DATA_OUT_SIZE = tc.get_res_word(test_dir, run_name)

    if (SPECT_OP_STATUS):
        print("SPECT_OP_STATUS:", hex(SPECT_OP_STATUS))
        return 0

    if (SPECT_OP_DATA_OUT_SIZE != 80):
        print("SPECT_OP_DATA_OUT_SIZE:", SPECT_OP_DATA_OUT_SIZE)
        return 0

    ########################################################################################################
    #   Read and Check
    ########################################################################################################

    l3_result = tc.read_output(test_dir, run_name, (outsrc<<12), 1)

    if (l3_result != 0xc3):
        print("L3 RESULT:", hex(l3_result))
        return 0

    signature = tc.read_output(test_dir, run_name, (outsrc<<12)+0x10, (SPECT_OP_DATA_OUT_SIZE-16)//4, string=True)

    return sign_ref == signature

if __name__ == "__main__":

    args = tc.parser.parse_args()
    seed = tc.set_seed(args)
    rn.seed(seed)
    print("seed:", seed)

    ret = 0

    ops_cfg = tc.get_ops_config()
    test_name = "eddsa_sequence"

    test_dir = tc.make_test_dir(test_name)

    k = rn.randint(0, 2**256-1).to_bytes(32, 'little')
    s, prefix, A = ed25519.key_gen(k)

    sch = int.to_bytes(rn.randint(0, 2**256-1), 32, 'big')
    scn = int.to_bytes(rn.randint(0, 2**32-1), 4, 'little')

    slot = rn.randint(0, 7)

    ########################################################################################################
    #   Test message len >= 64
    ########################################################################################################

    msg_bitlen = rn.randint(64, 200)*8
    message = int.to_bytes(rn.getrandbits(msg_bitlen), msg_bitlen//8, 'big')

    if not eddsa_sequence(s, prefix, A, slot, sch, scn, message, "_big"):
        tc.print_failed()
        ret = 1
    else:
        tc.print_passed()

    ########################################################################################################
    #   Test message len < 64
    ########################################################################################################

    msg_bitlen = rn.randint(1, 63)*8
    message = int.to_bytes(rn.getrandbits(msg_bitlen), msg_bitlen//8, 'big')

    if not eddsa_sequence(s, prefix, A, slot, sch, scn, message, "_small"):
        tc.print_failed()
        ret = 1
    else:
        tc.print_passed()

    if not eddsa_sequence(s, prefix, A, slot, sch, scn, message, "_empty_slot"):
        tc.print_failed()
        ret = 1
    else:
        tc.print_passed()

    if not eddsa_sequence(s, prefix, A, slot, sch, scn, message, "_invalid_curve"):
        tc.print_failed()
        ret = 1
    else:
        tc.print_passed()

    if "TS_SPECT_FW_TEST_DONT_DUMP" in os.environ.keys():
        os.system(f"rm -r {test_dir}")

    sys.exit(ret)
