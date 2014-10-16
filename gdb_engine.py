# unmask_jemalloc - De Mysteriis Dom jemalloc
# 
# Copyright (c) 2014 Patroklos Argyroudis <argp at domain census-labs.com>
# Copyright (c) 2014 Chariton Karamitas <huku at domain census-labs.com>

import sys
import resource

try:
    import gdb
except ImportError:
    print('[unmask_jemalloc] error: only usable from within gdb')
    sys.exit()

def get_page_size():
    return resource.getpagesize()

def offsetof(struct_name, member_name):
    expr = '(size_t)&(((%s *)0)->%s) - (size_t)((%s *)0)' % \
        (struct_name, member_name, struct_name)
    return to_int(gdb.parse_and_eval(expr))

def sizeof(type_name):
    return to_int(gdb.parse_and_eval('sizeof(%s)' % (type_name)))

# EOF
