# unmask_jemalloc - De Mysteriis Dom jemalloc

import sys
import resource

true = True
false = False
none = None

sys.path.append('.')

import util

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
        
    return util.to_int(gdb.parse_and_eval(expr))

def sizeof(type_name):
    return util.to_int(gdb.parse_and_eval('sizeof(%s)' % (type_name)))

def get_value(symbol):
    return gdb.parse_and_eval(symbol)

def eval_expr(expr):
    return gdb.parse_and_eval(expr)

def execute(expr):
    return gdb.execute(expr, to_string = true)

def read_memory(addr, size, proc):
    return proc.read_memory(addr, size)

def search(start_addr, end_addr, dword):
    search_expr = 'find %#x, %#x, %s'
    results = []

    search_str = search_expr % (start_addr, end_addr, dword)
    out_str = gdb.execute(search_str, to_string = true)
    str_results = out_str.split('\n')

    for str_result in str_results:
        if str_result.startswith('0x'):
            results.append((str_result, start_addr))

    return results

# EOF
