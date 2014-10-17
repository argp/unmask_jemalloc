# unmask_jemalloc - De Mysteriis Dom jemalloc

import sys
import warnings
import platform

sys.path.append('.')

INT_SIZE = 4        # on all tested platforms

def buf_to_le(buf):
    # this function is from seanhn's tcmalloc_gdb
    tmp = 0

    for i in range(0, len(buf)):
        tmp |= (ord(buf[i]) << i * 8)

    return tmp

def get_dword_size():
    # ugly but portable
    (arch, exe) = platform.architecture()

    if arch.startswith('64'):
        return 8
    else:
        return 4

def to_int(val):
    sval = str(val)

    # XXX: this must handle windbg's "?? sizeof" return string

    if sval.startswith('0x'):
        return int(sval, 16)
    else:
        return int(sval)

# unit testing
if __name__ == '__main__':
    print('[unmask_jemalloc] unit testing not implemented yet')
    sys.exit(0)

# EOF
