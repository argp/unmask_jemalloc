# unmask_jemalloc - De Mysteriis Dom jemalloc

import sys
import resource

sys.path.append('.')

import gdb_driver

try:
    import gdb
except ImportError:
    print('[unmask_jemalloc] gdb_engine is only usable from within gdb')
    sys.exit()

def get_page_size():
    return resource.getpagesize()

def offsetof(struct_name, member_name):
    expr = '(size_t)&(((%s *)0)->%s) - (size_t)((%s *)0)' % \
        (struct_name, member_name, struct_name)
        
    return to_int(gdb.parse_and_eval(expr))

def sizeof(type_name):
    return to_int(gdb.parse_and_eval('sizeof(%s)' % (type_name)))

def get_value(symbol):
    return gdb.parse_and_eval(symbol)

def eval_expr(expr):
    return gdb.parse_and_eval(expr)

def execute(expr):
    return gdb.execute(expr, to_string = true)

def read_memory(addr, size)
    global proc # defined and assigned in gdb_driver
    proc.read_memory(addr, size)

# EOF
