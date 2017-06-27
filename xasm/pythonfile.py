import time
from struct import pack
from xdis.magics import magics

def write_pycfile(pyc_file, python_version, code_list):
    with open(pyc_file, 'w') as fp:
        fp.write(magics[python_version])
        fp.write(pack('I', int(time.time())))
        # In Python 3 you need to write out the size mod 2**32 here
        from xdis.marsh import dumps
        for co in code_list:
            fp.write(dumps(co))
    print("Wrote %s" % pyc_file)
