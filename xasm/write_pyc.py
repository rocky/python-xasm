import xdis
from xdis import PYTHON3
from xdis.magics import magics
from xdis.marsh import dumps
from struct import pack
import time

def write_pycfile(fp, code_list, timestamp=int(time.time()),
                  version=xdis.PYTHON_VERSION):
    fp.write(magics[version])
    fp.write(pack('I', timestamp))
    if version > 3.2:
        fp.write(pack('I', 0))
    for co in code_list:
        try:
            co_obj = dumps(co, python_version=str(version))
            if PYTHON3 and version < 3.0:
                co_obj = str.encode(co_obj)
                pass

            fp.write(co_obj)
        except:
            pass
