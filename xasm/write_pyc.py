import xdis
from xdis import magic2int
from xdis.marsh import dumps
from xdis.magics import magics
from struct import pack
from xdis.version_info import PYTHON3, version_tuple_to_str
import time


def write_pycfile(fp, code_list, timestamp=None, version_triple=xdis.PYTHON_VERSION_TRIPLE):

    version_str = version_tuple_to_str(version_triple, end=2)
    magic_bytes = magics[version_str]
    magic_int = magic2int(magic_bytes)
    fp.write(magic_bytes)

    if timestamp is None:
        timestamp = int(time.time())
    write_source_size = version_triple >= (3, 3)
    if version_triple >= (3, 7):
        if magic_int == 3393:
            fp.write(pack("I", timestamp))
            fp.write(pack("I", 0))
        else:
            # PEP 552. https://www.python.org/dev/peps/pep-0552/
            # 0 in the lowest-order bit means used old-style timestamps
            fp.write(pack("<I", 0))
            fp.write(pack("<I", timestamp))
    else:
        fp.write(pack("<I", timestamp))

    if write_source_size:
        fp.write(pack("<I", 0))  # size mod 2**32

    for co in code_list:
        try:
            co_obj = dumps(co, python_version=version_triple)
            if PYTHON3 and version_triple < (3, 0):
                co_obj = str.encode(co_obj)
                pass

            fp.write(co_obj)
        except Exception:
            pass
