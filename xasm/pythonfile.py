import time
from struct import pack
from xdis.magics import magics
from xdis import PYTHON3

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
