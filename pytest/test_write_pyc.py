import os
import os.path as osp
import sys
from tempfile import NamedTemporaryFile

from xdis import PYTHON3, PYTHON_VERSION_TRIPLE, load_module

import pytest
from xasm.write_pyc import write_pycfile


def get_srcdir() -> str:
    filename = osp.normcase(os.path.dirname(__file__))
    return osp.realpath(filename)


src_dir = get_srcdir()
os.chdir(src_dir)


@pytest.mark.skipif(
    not PYTHON3,
    reason="test skipped because Python 2.x has problems creating Python 3.x files",
)
@pytest.mark.skipif(sys.platform in ("win32",), reason="Test does not work on Windows?")
def test_roundtrip3() -> None:
    fp = NamedTemporaryFile(mode="wb+", suffix=".pyc", prefix="test_pyc-", delete=False)
    orig_path = "testdata/test_pyc.pyc"
    version, timestamp, magic_int, co, is_pypy, source_size, sip_hash = load_module(
        orig_path
    )
    write_pycfile(fp, [co], timestamp, version)
    new_path = fp.name
    size = fp.tell()
    fp.close()
    print("Wrote Python %s bytecode file %s; %d bytes" % (version, fp.name, size))
    old_fp = open(orig_path, "rb")
    new_fp = open(new_path, "rb")
    if PYTHON_VERSION_TRIPLE < (3, 7):
        compare_size = 590
        assert old_fp.read(compare_size) == new_fp.read(compare_size)
    else:
        print("Skipped until we work out what's up with xdis unmarshal")
    os.unlink(new_path)


if __name__ == "__main__":
    test_roundtrip3()
