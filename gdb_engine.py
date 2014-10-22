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

# gdb expressions for parsing arenas
arena_expr = 'arenas[%d]'
arena_reg_size_expr = 'arenas[%d].bins[%d].reg_size'
arena_reg0_offset_expr = 'arenas[%d].bins[%d].reg0_offset'
arena_bin_info_reg_size_expr = 'arena_bin_info[%d].reg_size'
arena_bin_info_nregs_expr = 'arena_bin_info[%d].nregs'
arena_bin_info_run_size_expr = 'arena_bin_info[%d].run_size'
arena_runcur_expr = 'arenas[%d].bins[%d].runcur'
arena_runcur_bin_expr = '&arenas[%d].bins[%d]'

# gdb expressions for parsing all runs and their regions
chunk_map_expr = 'x/%d%sx ((arena_chunk_t *)%#x)->map'

# gdb expressions for parsing current runs
regs_mask_expr = 'x/%dbt arenas[%d].bins[%d].runcur.regs_mask'

# gdb expressions for parsing chunks
chunk_rtree_root_expr = 'chunk_rtree.root'
chunk_rtree_height_expr = 'chunk_rtree.height'
chunk_rtree_level2bits_expr = 'chunk_rtree.level2bits[%d]'
chunk_radix_expr = 'x/%d%sx %#x'
chunk_arena_expr = '((arena_chunk_t *)%#x)->arena'

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
