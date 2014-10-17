# unmask_jemalloc - De Mysteriis Dom jemalloc

import os
import sys
import warnings

sys.path.append('.')

import jemalloc
import util

true = True
false = False

# globals
jeheap = jemalloc.jemalloc()
parsed = false
dbg_engine = ''

try:
    import gdb
    import gdb_engine as dbg
    dbg_engine = 'gdb' # XXX: try _not_ to use this
except ImportError:
    # XXX: try to import other debugger python engine(s) here
    print('[unmask_jemalloc] error: only usable from within gdb at the moment')
    sys.exit()

# parse jemalloc configuration options
def jeparse_options():
    global jeheap

    # thread magazine caches (disabled on firefox)
    try:
        opt_mag = dbg.get_value('opt_mag')
    except RuntimeError:
        opt_mag = 0

    try:
        opt_tcache = dbg.get_value('opt_tcache')
    except RuntimeError:
        opt_tcache = 0

    try:
        opt_lg_tcache_nslots = \
            dbg.get_value('opt_lg_tcache_nslots')
    except RuntimeError:
        opt_lg_tcache_nslots = 0

    if opt_mag != 0 or opt_tcache != 0 or opt_lg_tcache_nslots != 0:
        jeheap.MAGAZINES = true

    if jeheap.MAGAZINES == true:
        try:
            mag_rag_t_size = dbg.sizeof('mag_rack_t')
            bin_mags_t_size = dbg.sizeof('bin_mags_t')
                
            jeheap.magrack_size = \
                    mag_rag_t_size + (bin_mags_t_size * (jeheap.nbins - 1))

        except RuntimeError:
            # standalone variant
            jeheap.STANDALONE = true

            tcache_t_size = dbg.sizeof('tcache_t')
            tcache_bin_t_size = dbg.sizeof('tcache_bin_t')

            jemalloc.magrack_size = \
                    tcache_t_size + (tcache_bin_t_size * (jeheap.nbins - 1))

# parse general jemalloc information
def jeparse_general():
    global jeheap

    try:
        jeheap.narenas = util.to_int(dbg.get_value('narenas'))
    except RuntimeError:
        print('[unmask_jemalloc] error: symbol narenas not found')
        sys.exit()

    try:
        jeheap.nbins = util.to_int(dbg.get_value('nbins'))
    except RuntimeError:
        # XXX: these are firefox specific, we must add support for more
        #      jemalloc variants in the future
        if sys.platform == 'darwin' or sys.platform == 'win32':
            jeheap.ntbins = util.to_int(dbg.get_value('ntbins'))
            jeheap.nsbins = util.to_int(dbg.get_value('nsbins'))
            jeheap.nqbins = util.to_int(dbg.get_value('nqbins'))
            jeheap.nbins = jeheap.ntbins + jeheap.nsbins + jeheap.nqbins
        else:
            if jeheap.DWORD_SIZE == 4:
                jeheap.nbins = 36
            elif jeheap.DWORD_SIZE == 8:
                jeheap.nbins = 35

    # XXX: figure out how to calculate the chunk size correctly, this is
    #      firefox specific
    jeheap.chunk_size = 1 << 20

# parse jemalloc arena information
def jeparse_arenas():
    global jeheap

    jeheap.arenas[:] = []

    for i in range(0, jeheap.narenas):
        current_arena = jemalloc.arena(0, i, [])

        try:
            current_arena.addr = \
                util.to_int(dbg.eval_expr('arenas[%d]' % (i)))
        except:
            print('[unmask_jemalloc] error: cannot evaluate arenas[%d]') % (i)
            sys.exit()

        for j in range(0, jeheap.nbins):
            nrg = 0
            run_sz = 0
            reg_size = 0
            reg_offset = 0
            end_addr = 0

            try:
                expr = 'arenas[%d].bins[%d].reg_size' % (i, j)
                reg_size = \
                    util.to_int(dbg.eval_expr(expr))
               
                expr = 'arenas[%d].bins[%d].reg0_offset' % (i, j) 
                reg_offset = \
                    util.to_int(dbg.eval_expr(expr))

            except RuntimeError:
                # XXX: for now assume it's a standalone variant; we
                #      need to do some error checking here too.
                jeheap.STANDALONE = true

                expr = 'arena_bin_info[%d].reg_size' % (j)
                reg_size = \
                    util.to_int(dbg.eval_expr(expr))

                expr = 'arena_bin_info[%d].nregs' % (j)
                nrg = \
                    util.to_int(dbg.eval_expr(expr))

                expr = 'arena_bin_info[%d].run_size' % (j)
                run_sz = \
                    util.to_int(dbg.eval_expr(expr))

            try:
                expr = 'arenas[%d].bins[%d].runcur' % (i, j)
                runcur_addr = runcur = \
                    util.to_int(dbg.eval_expr(expr))

                end_addr = runcur_addr + run_sz

                if runcur != 0:
                    current_run = \
                        jemalloc.arena_run(runcur, end_addr, run_sz, 0, \
                            int(reg_size), reg_offset, nrg, 0, [])

                    current_bin = jemalloc.arena_bin(0, j, current_run)
                    current_bin.addr = \
                        util.to_int(dbg.eval_expr('&arenas[%d].bins[%d]' % (i, j)))

                    current_arena.bins.append(current_bin)

                else:
                    # no regions for this size class yet, therefore no runcur
                    current_run = jemalloc.arena_run()
                    current_bin = jemalloc.arena_bin(0, j, current_run)
                    current_arena.bins.append(current_bin)

            except RuntimeError:
                current_run = jemalloc.arena_run()
                current_bin = jemalloc.arena_bin(0, j, current_run)
                current_arena.bins.append(current_bin)
                continue

        # add arena to the list of arenas
        jeheap.arenas.append(current_arena)

# parse the metadata of all runs and their regions
def jeparse_all_runs(proc):
    global jeheap

    # number of pages a chunk occupies
    chunk_npages = jeheap.chunk_size >> 12

    # offset of bits in arena_chunk_map_t in double words
    bitmap_offset = \
        util.offsetof('arena_chunk_map_t', 'bits') / jeheap.DWORD_SIZE

    # number of double words occupied by an arena_chunk_map_t
    chunk_map_dwords = \
        (bitmap_offset / jeheap.DWORD_SIZE) + 1

    # prefix to use in gdb's examine command
    if jeheap.DWORD_SIZE == 8:
        dword_fmt = 'g'
    else:
        dword_fmt = 'w'

    # the 12 least significant bits of each bitmap entry hold
    # various flags for the corresponding run
    flags_mask = (1 << 12) - 1

    # delete the heap's runs' array
    jeheap.runs[:] = []

    for chunk in jeheap.chunks:
        if not chunk.arena:
            continue

        try:
            # parse the whole map at once to avoid gdb's delays
            expr = 'x/%d%sx ((arena_chunk_t *)%#x)->map' % \
                (chunk_npages * chunk_map_dwords, dword_fmt, chunk.addr)
        except:
            print('[unmask_jemalloc] error: cannot read bitmap from chunk %#x' % (chunk.addr))
            sys.exit()

        lines = (dbg.execute(expr)).split('\n')

        dwords = []
        i = 0

        for line in lines:
            dwords += [int(dw, 16) for dw in line[line.find(':') + 1:].split()]

        bitmap = [dwords[i] for i in range(int(bitmap_offset), \
                int(len(dwords)), int(bitmap_offset + 1))]

        # traverse the bitmap
        for mapelm in bitmap:
            flags = mapelm & flags_mask

            # flags == 1 means the chunk is small and the rest of the bits
            # hold the actual run address
            if flags == 1:
                addr = mapelm & ~flags_mask
                size = dbg.get_page_size()

            # flags = 3 indicates a large chunk; calculate the run's address
            # directly from the map element index and extract the run's size 
            elif flags == 3:
                addr = chunk.addr + i * dbg.get_page_size()
                size = mapelm & ~flags_mask

            # run is not allocated? skip it
            else:
                continue
    
            if addr not in [r.start for r in jeheap.runs]:
                # XXX: we need to parse run headers here with a
                #      dedicated function
                new_run = jemalloc.arena_run(addr, 0, size, 0, 0, 0, 0, 0, [])
                jeheap.runs.append(new_run)


# parse metadata of current runs and their regions
def jeparse_runs(proc):
    global jeheap

    for i in range(0, len(jeheap.arenas)):
        for j in range(0, len(jeheap.arenas[i].bins)):

            try:
                run_addr = jeheap.arenas[i].bins[j].run.start
                    
                bin_addr = \
                    util.buf_to_le(dbg.read_memory(run_addr, jeheap.DWORD_SIZE))

                jeheap.arenas[i].bins[j].run.bin = bin_addr

                if jeheap.STANDALONE == false:
                    jeheap.arenas[i].bins[j].run.size = \
                        util.buf_to_le(dbg.read_memory(bin_addr + \
                            (6 * jeheap.DWORD_SIZE), jeheap.DWORD_SIZE))

                    jeheap.arenas[i].bins[j].run.end = \
                        run_addr + jeheap.arenas[i].bins[j].run.size

                    jeheap.arenas[i].bins[j].run.total_regions = \
                        util.buf_to_le(dbg.read_memory(bin_addr + \
                            (7 * jeheap.DWORD_SIZE), util.INT_SIZE))

            except RuntimeError:
                continue

            # XXX: this isn't correct on jemalloc standalone *debug* variant
            try:
                jeheap.arenas[i].bins[j].run.free_regions = \
                    util.buf_to_le(dbg.read_memory(run_addr + \
                        jeheap.DWORD_SIZE + util.INT_SIZE, util.INT_SIZE))
            except RuntimeError:
                jeheap.arenas[i].bins[j].run.free_regions = 0
                continue

            if jeheap.arenas[i].bins[j].run.free_regions < 0:
                jeheap.arenas[i].bins[j].run.free_regions = 0

            # delete the run's regions
            jeheap.arenas[i].bins[j].run.regions[:] = []
            
            # the run's regions
            reg0_offset = jeheap.arenas[i].bins[j].run.reg0_offset;
            first_region_addr = reg0_addr = run_addr + reg0_offset

            regs_mask_bits = \
                (jeheap.arenas[i].bins[j].run.total_regions / 8) + 1

            regs_mask_str = \
                dbg.execute('x/%dbt arenas[%d].bins[%d].runcur.regs_mask' % \
                    (regs_mask_bits, i, j))

            regs_mask = ''

            for line in regs_mask_str.splitlines():
                line = line[line.find(':') + 1 : line.find('\n')]
                line = line.replace('\n', '')
                line = line.replace('\t', '')
                line = line.replace(' ', '')
                regs_mask += line

            jeheap.arenas[i].bins[j].run.regs_mask = regs_mask

            first_region = jemalloc.region(0, first_region_addr, \
                int(jeheap.arenas[i].bins[j].run.regs_mask[0]))

            addr = first_region.addr

            try:
                first_region.content_preview = \
                    hex(util.buf_to_le(dbg.read_memory(addr, \
                        util.INT_SIZE))).rstrip('L')
            except RuntimeError:
                continue

            jeheap.arenas[i].bins[j].run.regions.append(first_region)

            for k in range(1, jeheap.arenas[i].bins[j].run.total_regions):
                try:
                    current_region = jemalloc.region(k, 0, \
                        int(jeheap.arenas[i].bins[j].run.regs_mask[k]))
                except:
                    current_region = jemalloc.region(k, 0, 0)

                addr = current_region.addr = \
                    reg0_addr + (k * jeheap.arenas[i].bins[j].run.region_size)
                
                try:
                    current_region.content_preview = \
                        hex(util.buf_to_le(dbg.read_memory(addr, \
                            util.INT_SIZE))).rstrip('L')
                except:
                    continue

                jeheap.arenas[i].bins[j].run.regions.append(current_region)

# parse all jemalloc chunks
def jeparse_chunks():
    global jeheap

    # delete the chunks' list
    jeheap.chunks[:] = []

    try:
        root = gdbutil.to_int(gdb.parse_and_eval('chunk_rtree.root'))
        height = gdbutil.to_int(gdb.parse_and_eval('chunk_rtree.height'))

        level2bits = []
        for i in range(0, height):
            expr = 'chunk_rtree.level2bits[%d]' % (i)
            level2bits.append(gdbutil.to_int(gdb.parse_and_eval(expr)))
    except:
        print('[unmask_jemalloc] error: cannot parse chunk radix tree')
        sys.exit()

    # check if we're running on x86_64
    if jeheap.DWORD_SIZE == 8:
        dw_fmt = 'g'
    else:
        dw_fmt = 'w'

    # parse the radix tree using a stack
    stack = [(root, 0)]
    while len(stack):
        (node, node_height) = stack.pop()
        child_cnt = 1 << level2bits[node_height]
        dump = gdb.execute('x/%d%sx %#x' % (child_cnt, dw_fmt, node), to_string = true)

        for line in dump.split('\n'):
            line = line[line.find(':') + 1:]

            for address in line.split():
                address = int(address, 16)

                if address != 0:
                    # leaf nodes hold pointers to actual values
                    if node_height == height - 1:
                        expr = '((arena_chunk_t *)%#x)->arena' % address
                        arena = gdbutil.to_int(gdb.parse_and_eval(expr))
 
                        exists = false
                        if arena in [i.addr for i in jeheap.arenas]:
                            exists = true

                        if exists:
                            jeheap.chunks.append(jemalloc.arena_chunk(address, arena))
                        else:
                            jeheap.chunks.append(jemalloc.arena_chunk(address))

                    # non-leaf nodes are inserted in the stack
                    else:
                        stack.append((address, node_height + 1))


# our old workhorse, now broken in pieces
def jeparse(proc):
    global jeheap
    global parsed

    parsed = false
    print('[unmask_jemalloc] parsing structures from memory...')

    jeparse_options()
    jeparse_general()
    jeparse_arenas()
    jeparse_runs(proc)
    jeparse_chunks()
    jeparse_all_runs(proc)

    parsed = true
    print('[unmask_jemalloc] structures parsed')


########## exported gdb commands ##########

class jemalloc_help(gdb.Command):
    '''Details about the commands provided by unmask_jemalloc'''

    def __init__(self):
        gdb.Command.__init__(self, 'jehelp', gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        print('[unmask_jemalloc] De Mysteriis Dom jemalloc')
        print('[unmask_jemalloc] %s\n' % (jemalloc.VERSION))
        print('[unmask_jemalloc] available commands:')
        print('[unmask_jemalloc]   jechunks               : dump info on all available chunks')
        print('[unmask_jemalloc]   jearenas               : dump info on jemalloc arenas')
        print('[unmask_jemalloc]   jeruns [-c]            : dump info on jemalloc runs (-c for current runs only)')
        print('[unmask_jemalloc]   jebins                 : dump info on jemalloc bins')
        print('[unmask_jemalloc]   jeregions <size class> : dump all current regions of the given size class')
        print('[unmask_jemalloc]   jesearch [-c] <hex>    : search the heap for the given hex value (-c for current runs only)')
        print('[unmask_jemalloc]   jedump [filename]      : dump all available info to screen (default) or file')
        print('[unmask_jemalloc]   jeparse                : (re)parse jemalloc structures from memory')
        print('[unmask_jemalloc]   jeversion              : output version number')
        print('[unmask_jemalloc]   jehelp                 : this help message')


class jemalloc_version(gdb.Command):
    '''Output version number'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeversion', gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        print('[unmask_jemalloc] %s' % (jemalloc.VERSION))


class jemalloc_parse(gdb.Command):
    '''Parse jemalloc structures from memory'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeparse', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        jeparse(self.proc)

class jemalloc_dump(gdb.Command):
    '''Dump all available jemalloc info to screen (default) or to file'''

    def __init__(self):
        gdb.Command.__init__(self, 'jedump', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if arg == '':
            print('[unmask_jemalloc] dumping all jemalloc info to screen')
        else:
            print('[unmask_jemalloc] dumping all jemalloc info to file %s' % (arg))

            if os.path.exists(arg):
                print('[unmask_jemalloc] error: file %s already exists' % (arg))
                return

            try:
                sys.stdout = open(arg, 'w')
            except:
                print('[unmask_jemalloc] error opening file %s for writing' % (arg))
            
        if parsed == false:
            jeparse(self.proc)

        # general jemalloc info
        print(jeheap)
        print('')

        # info on chunks
        for chunk in jeheap.chunks:
            print(chunk)
            
        print('')

        # info on arenas
        for i in range(0, len(jeheap.arenas)):
            print(jeheap.arenas[i])
            
            print('')

            # info on current runs and bins
            for j in range(0, len(jeheap.arenas[i].bins)):
                print(jeheap.arenas[i].bins[j].run)
                print(jeheap.arenas[i].bins[j])

                # info on current regions
                for k in range(0, len(jeheap.arenas[i].bins[j].run.regions)):
                    print('[unmask_jemalloc] [region %03d] [%#x]' % \
                        (k, jeheap.arenas[i].bins[j].run.regions[k].addr))

                print('')

        # reset stdout
        if arg != '':
            sys.stdout = sys.__stdout__


class jemalloc_chunks(gdb.Command):
    '''Dump info on all available chunks'''

    def __init__(self):
        gdb.Command.__init__(self, 'jechunks', gdb.COMMAND_OBSCURE)
       
        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if parsed == false:
            jeparse(self.proc)

        for chunk in jeheap.chunks:
            print(chunk)


class jemalloc_arenas(gdb.Command):
    '''Dump info on jemalloc arenas'''

    def __init__(self):
        gdb.Command.__init__(self, 'jearenas', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if parsed == false:
            jeparse(self.proc)

        print(jeheap)


class jemalloc_runs(gdb.Command):
    '''Dump info on jemalloc current runs'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeruns', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if parsed == false:
            jeparse(self.proc)

        arg = arg.split()
        if len(arg) >= 1 and arg[0] == '-c':
            current_runs = true
        else:
            current_runs = false

        if current_runs == true:
            print('[unmask_jemalloc] listing current runs only')

            for i in range(0, len(jeheap.arenas)):
                print(jeheap.arenas[i])
    
                for j in range(0, len(jeheap.arenas[i].bins)):
                    print(jeheap.arenas[i].bins[j].run)

        else:
            print('[unmask_jemalloc] listing all allocated runs')

            total_runs = len(jeheap.runs)
            print('[unmask_jemalloc] [total runs %d]' % (total_runs))

            for i in range(0, total_runs):
                print('[unmask_jemalloc] [run %#x] [size %07d]' % \
                    (jeheap.runs[i].start, jeheap.runs[i].size))


class jemalloc_bins(gdb.Command):
    '''Dump info on jemalloc bins'''

    def __init__(self):
        gdb.Command.__init__(self, 'jebins', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if parsed == false:
            jeparse(self.proc)

        for i in range(0, len(jeheap.arenas)):
            print(jeheap.arenas[i])

            for j in range(0, len(jeheap.arenas[i].bins)):
                print(jeheap.arenas[i].bins[j])


class jemalloc_regions(gdb.Command):
    '''Dump all current regions of the given size class'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeregions', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if arg == '':
            print('[unmask_jemalloc] usage: jeregions <size class>')
            print('[unmask_jemalloc] for example: jeregions 1024')
            return

        if parsed == false:
            jeparse(self.proc)

        size_class = int(arg)

        print('[unmask_jemalloc] dumping all regions of size class %d' % (size_class))
        found = false

        for i in range(0, len(jeheap.arenas)):
            for j in range(0, len(jeheap.arenas[i].bins)):
                
                if jeheap.arenas[i].bins[j].run.region_size == size_class:
                    found = true
                    print(jeheap.arenas[i].bins[j].run)
                    
                    # the bitmask of small-sized runs is too big to display
                    # print '[unmask_jemalloc] [regs_mask %s]' % (jeheap.arenas[i].bins[j].run.regs_mask)

                    for k in range(0, len(jeheap.arenas[i].bins[j].run.regions)):
                        print(jeheap.arenas[i].bins[j].run.regions[k])

        if found == false:
            print('[unmask_jemalloc] no regions found for size class %d' % (size_class))


class jemalloc_search(gdb.Command):
    '''Search the jemalloc heap for the given hex value'''

    def __init__(self):
        gdb.Command.__init__(self, 'jesearch', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        global jeheap

        if arg == '':
            print('[unmask_jemalloc] usage: jesearch [-c] <hex value>')
            print('[unmask_jemalloc] Use -c to search current runs only')
            print('[unmask_jemalloc] for example: jesearch 0x41424344')
            return

        arg = arg.split()
        if len(arg) >= 2 and arg[0] == '-c':
            current_runs = true
            search_for = arg[1]
        else:
            current_runs = false
            search_for = arg[0]

        if parsed == false:
            jeparse(self.proc)

        results = []
        found = false

        if current_runs == true:
            print('[unmask_jemalloc] searching all current runs for %s' % (search_for))
    
            for i in range(0, len(jeheap.arenas)):
                for j in range(0, len(jeheap.arenas[i].bins)):
                    try:
                        out_str = gdb.execute('find %#x, %#x, %s' % \
                            (jeheap.arenas[i].bins[j].run.start, \
                            jeheap.arenas[i].bins[j].run.end, \
                            search_for), \
                            to_string = true)
                    except:
                        continue
    
                    str_results = out_str.split('\n')
    
                    for str_result in str_results:
                        if str_result.startswith('0x'):
                            found = true
                            results.append((str_result, jeheap.arenas[i].bins[j].run.start))
        else:
            print('[unmask_jemalloc] searching all chunks for %s' % (search_for))

            for chunk in jeheap.chunks:
                try:
                    out_str = gdb.execute('find %#x, %#x, %s' % \
                        (chunk.addr, chunk.addr + jeheap.chunk_size, search_for), \
                        to_string = true)
                except:
                    continue

                str_results = out_str.split('\n')
    
                for str_result in str_results:
                    if str_result.startswith('0x'):
                        found = true
                        results.append((str_result, chunk.addr))

        if found == false:
            print('[unmask_jemalloc] value %s not found' % (search_for))
            return

        for (what, where) in results:
            if current_runs == true:
                print('[unmask_jemalloc] found %s at %s (run %#x)' % \
                    (search_for, what, where))
            else:
                print('[unmask_jemalloc] found %s at %s (chunk %#x)' % \
                    (search_for, what, where))


# required for classes that implement gdb commands
jemalloc_parse()
jemalloc_dump()
jemalloc_chunks()
jemalloc_arenas()
jemalloc_runs()
jemalloc_bins()
jemalloc_regions()
jemalloc_search()
jemalloc_help()
jemalloc_version()

# EOF
