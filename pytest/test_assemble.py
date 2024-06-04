"""
Test xasm.assemble code
"""

from xdis.opcodes import (opcode_15, opcode_27, opcode_35, opcode_36,
                          opcode_36pypy, opcode_312)

from xasm.assemble import append_operand


def test_append_operand():

    def check_one(expected_bytecode_len: int, operand_value):
        bytecode = []
        append_operand(
            bytecode,
            operand_value,
            opc.EXTENDED_ARG_SHIFT,
            opc.ARG_MAX_VALUE,
            opc.EXTENDED_ARG,
        )

        assert len(bytecode) > 0
        assert len(bytecode) == expected_bytecode_len
        shift_value = 1
        extended_arg_value = 0
        low_order_value = bytecode.pop()
        assert low_order_value <= opc.ARG_MAX_VALUE

        if len(bytecode):
            assert bytecode[0] == opc.EXTENDED_ARG

        while len(bytecode) > 1:
            shift_value <<= opc.EXTENDED_ARG_SHIFT
            extended_arg_value += bytecode.pop() * shift_value

        assert extended_arg_value <= operand_value
        got_value = extended_arg_value + low_order_value
        assert got_value == operand_value

    for opc in (
        opcode_15,
        opcode_27,
        opcode_35,
        opcode_36,
        opcode_312,
        opcode_36pypy,
        opcode_312,
    ):
        for operand_value in 0, 11, 255:
            check_one(1, operand_value)
        for operand_value in 256, 413, 900, 4000, 1001, 65535:
            print(opc, operand_value)
            bytecode_len = 1 if opc.version_tuple < (3, 6) else 3
            check_one(bytecode_len, operand_value)
        for operand_value in 65536, 200000:
            print(opc, operand_value)
            check_one(3, operand_value)


if __name__ == "__main__":
    test_append_operand()
