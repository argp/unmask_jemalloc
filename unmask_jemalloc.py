# unmask_jemalloc - De Mysteriis Dom jemalloc
# 
# Copyright (c) 2012 Patroklos Argyroudis <argp at domain census-labs.com>
# Copyright (c) 2012 huku

try:
    import gdb
except ImportError:
    print '[unmask_jemalloc] this is only usable from within gdb'
    exit()

import sys

class unmask_jemalloc(gdb.Command):
    '''
    [De Mysteriis Dom jemalloc] [v0.3a]

    Spaghetti code full of heuristics and (black) magic numbers.
    Feel free to untangle it and bind its demons by submitting patches.

    The development of unmask_jemalloc will continue at:

    https://github.com/argp/unmask_jemalloc

    usage: unmask_jemalloc [options]
    options:

        [no options]    general jemalloc information, and information on
                        arenas, bins, runs and thread magazine caches

        runs            all the above, plus the metadata of current used
                        runs and their sizes
    
        all             all available information, i.e. all the above plus
                        individual region addresses
    '''

    def __init__(self):
        gdb.Command.__init__(self, 'unmask_jemalloc', gdb.COMMAND_OBSCURE)
        self._JEMALLOC_MAG = 0  # no thread magazines by default
        self._JEMALLOC_SA = 0   # standalone variant flag
        self._RUNHDR_SIZE = 64  # covers all thousand faces of jemalloc
        self._proc = gdb.inferiors()[0]

    def _buf_to_le(self, buf):
        # this function is from seanhn's tcmalloc_gdb
        tmp = 0
        for i in range(0, len(buf)):
            tmp |= (ord(buf[i]) << i * 8)

        return tmp

    def invoke(self, arg, from_tty):
        used_runs = set()
        all_flag = 0
        runs_flag = 0

        if arg == 'all':
            all_flag = 1
        elif arg == 'runs':
            runs_flag = 1

        narenas = int(gdb.parse_and_eval('narenas'))
        
        try:
            nbins = int(gdb.parse_and_eval('nbins'))
        except RuntimeError:
            # firefox jemalloc
            if sys.platform == 'darwin':
                nbins = 35
            else:
                # linux
                nbins = 24

        # general information
        print '\n[jemalloc] [number of arenas:\t\t%d]' % (narenas)
        print '[jemalloc] [number of bins:\t\t%d]' % (nbins)

        # thread magazine caches
        try:
            opt_mag = int(gdb.parse_and_eval('opt_mag'))
        except RuntimeError:
            opt_mag = 0

        try:
            opt_tcache = int(gdb.parse_and_eval('opt_tcache'))
        except RuntimeError:
            opt_tcache = 0

        try:
            opt_lg_tcache_nslots = int(gdb.parse_and_eval('opt_lg_tcache_nslots'))
        except RuntimeError:
            opt_lg_tcache_nslots = 0

        if opt_mag != 0 or opt_tcache != 0 or opt_lg_tcache_nslots != 0:
            self._JEMALLOC_MAG = 1

        if self._JEMALLOC_MAG == 1:
            try:
                magrack_size = \
                int(gdb.parse_and_eval('sizeof(mag_rack_t) + (sizeof(bin_mags_t) * (nbins - 1))'))
            except RuntimeError:
                # standalone version
                self._JEMALLOC_SA = 1
                magrack_size = \
                int(gdb.parse_and_eval('sizeof(tcache_t) + (sizeof(tcache_bin_t) * (nbins - 1))'))

            print '[jemalloc] [magazine rack/tcache size:\t%d]\n' % (magrack_size)
        else:
            print '[jemalloc] [no magazines/thread caches detected]\n'

        # bins, sizes and current runs
        for i in range(0, narenas):
            for j in range(0, nbins):
                nrg = 0
                run_sz = 0
                reg_size = 0

                try:
                    reg_size = \
                    gdb.parse_and_eval('arenas[%d].bins[%d].reg_size' % (i, j))
                except RuntimeError:
                    # standalone version
                    self._JEMALLOC_SA = 1
                    reg_size = gdb.parse_and_eval('arena_bin_info[%d].reg_size' % (j))
                    nrg = gdb.parse_and_eval('arena_bin_info[%d].nregs' % (j))
                    run_sz = gdb.parse_and_eval('arena_bin_info[%d].run_size' % (j))

                runcur = \
                gdb.parse_and_eval('arenas[%d].bins[%d].runcur' % (i, j))

                try:
                    if runcur != 0:
                        used_runs.add((runcur, nrg, run_sz, int(reg_size)))
                except RuntimeError:
                    pass

                try:
                    print '[jemalloc] [arena #%02d] [bin #%02d] [region size: 0x%0.4x] [current run at: %s]' \
                    % (i, j, reg_size, runcur)
                except RuntimeError:
                    pass

        if all_flag == 0 and runs_flag == 0:
            return

        # metadata of current used runs and their regions
        for (run, nregs, run_size, reg_sz) in used_runs:
            run_addr = int(str(run), 16)
            bin_addr = self._buf_to_le(self._proc.read_memory(run_addr, 4))

            if self._JEMALLOC_SA == 0:
                run_size = int(self._buf_to_le(self._proc.read_memory(bin_addr + 24, 4)))
                nregs = int(self._buf_to_le(self._proc.read_memory(bin_addr + 28, 4)))

            # fix me: this isn't correct on jemalloc standalone debug version
            free_nregs = int(self._buf_to_le(self._proc.read_memory(run_addr + 8, 4)))

            if runs_flag == 1:
                print '\n[jemalloc] [run %s] [from %s to %s]' \
                % (run, run, hex(run_addr + int(run_size))),
                
                if all_flag == 0:
                    continue

            print '\n[jemalloc] [run %s metadata] [run\'s bin: %s] [run size: %s]' \
            % (run, hex(bin_addr), run_size)

            for i in range(0, self._RUNHDR_SIZE, 4):
                metadata_buf = self._proc.read_memory(run_addr + i, 4)
                metadata = self._buf_to_le(metadata_buf)
                print '[jemalloc] [%s: %s]' % (hex(run_addr + i), hex(metadata))

            print '\n[jemalloc] [run %s regions] [regions: %s] [free regions: %s]' \
            % (run, nregs, free_nregs)

            run_addr_int = run_addr + int(str(40), 16)
            print '[jemalloc] [region #%03d] [%s]' \
            % (0, hex(run_addr_int))

            for i in range(1, nregs):
                print '[jemalloc] [region #%03d] [%s]' \
                % (i, hex(run_addr_int + int(str((i) * reg_sz))))

        print ''

unmask_jemalloc()

# EOF
