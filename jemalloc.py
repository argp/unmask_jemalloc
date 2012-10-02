# unmask_jemalloc - De Mysteriis Dom jemalloc
# 
# Copyright (c) 2012 Patroklos Argyroudis <argp at domain census-labs.com>
# Copyright (c) 2012 Chariton Karamitas <huku at domain census-labs.com>
# Copyright (c) 2012 Census, Inc. (http://www.census-labs.com/)

import sys
import warnings

sys.path.append('.')
import gdbutil

true = True
false = False

VERSION = 'v0.666 (bh-usa-2012)'

class jemalloc:

    def __init__(self, chunks = [], chunk_size = 0, \
        arenas = [], narenas = 0, runs = [], nbins = 0, \
        magrack_size = 0, magaz_flag = false, \
        standalone_flag = false):

        self.chunks = chunks
        self.chunk_size = chunk_size
        self.arenas = arenas
        self.narenas = narenas
        self.nbins = nbins
        self.magrack_size = magrack_size
        self.DWORD_SIZE = gdbutil.get_dword_size()
        self.runs = runs

        self.MAGAZINES = magaz_flag
        self.STANDALONE = standalone_flag

    def __str__(self):

        if self.MAGAZINES == false:
            return '[unmask_jemalloc] [jemalloc] [arenas %02d] [bins %02d]' \
                   ' [runs %02d]' % (self.narenas, self.nbins, len(self.runs))
        else:
            return '[unmask_jemalloc] [jemalloc] [arenas %02d] [bins %02d] ' \
                   '[runs %02d] [magazine rack/tcache size %04d]' % \
                    (self.narenas, self.nbins, len(self.runs), self.magrack_size)

class arena_chunk:

    def __init__(self, addr = 0, arena = 0):

        self.addr = addr
        self.arena = arena

    def __str__(self):

        if self.arena != 0:
            return '[unmask_jemalloc] [chunk %#x] [arena %#x]' % (self.addr, self.arena)
        else:
            return '[unmask_jemalloc] [chunk %#x] [orphan]' % (self.addr)


class arena_run:

    def __init__(self, start = 0, end = 0, size = 0, bin = 0, \
        region_size = 0, reg0_offset = 0, total_regions = 0, \
        free_regions = 0, regions = []):
        
        self.start = start
        self.end = end
        self.size = size
        self.bin = bin
        self.region_size = region_size
        self.reg0_offset = reg0_offset
        self.total_regions = total_regions
        self.free_regions = free_regions
        self.regions = regions
        self.regs_mask = ''

    def __str__(self):

        return '[unmask_jemalloc] [run %#x] [size %05d] [bin %#x] [region size %04d] ' \
               '[total regions %03d] [free regions %03d]' % \
                (self.start, self.size, self.bin, \
                 self.region_size, self.total_regions, self.free_regions)

class arena_bin:

    def __init__(self, addr, index, runcur):

        self.addr = addr
        self.index = index
        self.run = runcur

    def __str__(self):

        return '[unmask_jemalloc] [bin %02d (%#x)] [size class %04d] [runcur %#x]' % \
            (self.index, self.addr, self.run.region_size, self.run.start)

class region:

    def __init__(self, index = 0, addr = 0, is_free = 1):

        self.index = index
        self.addr = addr
        self.is_free = is_free
        self.content_preview = ''

    def __str__(self):

        str = '[unmask_jemalloc] [region %03d]' % (self.index)

        if self.is_free == 1:
            str += ' [free]'
        elif self.is_free == 0:
            str += ' [used]'

        if self.content_preview != '':
            str += ' [%#x] [%s]' % (self.addr, self.content_preview)
        else:
            str += ' [%#x]' % (self.addr)

        return str

class arena:

    def __init__(self, addr = 0, index = 0, bins = []):
        
        self.addr = addr
        self.index = index
        self.bins = bins

    def __str__(self):
        
        return '[unmask_jemalloc] [arena %02d (%#x)] [bins %02d]' % \
            (self.index, self.addr, len(self.bins))

# unit testing
if __name__ == '__main__':
    print '[unmask_jemalloc] unit testing not implemented yet'
    sys.exit(0)

# EOF
