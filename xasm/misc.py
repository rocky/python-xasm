import time
from struct import pack
from xdis.magics import magics
from xdis import PYTHON3
import xdis

def write_pycfile(pyc_file, python_version, code_list, timestamp=None):
    if PYTHON3:
        file_mode = 'wb'
    else:
        file_mode = 'w'

    with open(pyc_file, file_mode) as fp:
        fp.write(magics[python_version])
        if not timestamp :
            timestamp = int(time.time())
        fp.write(pack('I', timestamp))
        # In Python 3 you need to write out the size mod 2**32 here
        from xdis.marsh import dumps
        for co in code_list:
            fp.write(dumps(co))
    print("Wrote %s" % pyc_file)

def get_opcode(python_version):
    if python_version in "2.5 2.6 2.7".split():
        from xdis.code import Code2 as Code
        if python_version == '2.5':
            from xdis.opcodes import opcode_25 as opc
        elif python_version == '2.6':
            from xdis.opcodes import opcode_26 as opc
        else:
            from xdis.opcodes import opcode_27 as opc
            pass
    elif python_version in "3.3 3.4".split():
        from xdis.code import Code3 as Code
        if python_version == '3.4':
            from xdis.opcodes import opcode_33 as opc
        elif python_version == '3.4':
            from xdis.opcodes import opcode_34 as opc
    else:
        raise RuntimeError("Python version %s not supported yet" % python_version)
    return opc, Code
