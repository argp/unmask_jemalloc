# unmask_jemalloc - De Mysteriis Dom jemalloc
# 
# Copyright (c) 2014 Patroklos Argyroudis <argp at domain census-labs.com>
# Copyright (c) 2014 Chariton Karamitas <huku at domain census-labs.com>
# Copyright (c) 2014 Census, Inc. (http://www.census-labs.com/)

import sys
import warnings
import platform
import resource

sys.path.append('.')

from gdbwrap import *


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

def get_page_size():
    return resource.getpagesize()

def to_int(val):
    sval = str(val)

    if sval.startswith('0x'):
        return int(sval, 16)
    else:
        return int(sval)

def offsetof(struct_name, member_name):
    expr = '(size_t)&(((%s *)0)->%s) - (size_t)((%s *)0)' % \
        (struct_name, member_name, struct_name)
    return to_int(gdb.parse_and_eval(expr))

def sizeof(type_name):
    return to_int(gdb.parse_and_eval('sizeof(%s)' % (type_name)))

# unit testing
if __name__ == '__main__':
    print('[unmask_jemalloc] unit testing not implemented yet')
    sys.exit(0)

# EOF
