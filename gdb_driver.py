# unmask_jemalloc - De Mysteriis Dom jemalloc

import os
import sys
import warnings

sys.path.append('.')

import unmask_jemalloc

true = True
false = False
none = None

class jemalloc_help(gdb.Command):
    '''Details about the commands provided by unmask_jemalloc'''

    def __init__(self):
        gdb.Command.__init__(self, 'jehelp', gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        unmask_jemalloc.help()

class jemalloc_version(gdb.Command):
    '''Output version number'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeversion', gdb.COMMAND_OBSCURE)

    def invoke(self, arg, from_tty):
        unmask_jemalloc.version()

class jemalloc_parse(gdb.Command):
    '''Parse jemalloc structures from memory'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeparse', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        unmask_jemalloc.parse(proc = self.proc)

class jemalloc_dump(gdb.Command):
    '''Dump all available jemalloc info to screen (default) or to file'''

    def __init__(self):
        gdb.Command.__init__(self, 'jedump', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        if arg == '':
            screen = true
        else:
            screen = false

        unmask_jemalloc.dump_all(filename = arg, \
                dump_to_screen = screen, proc = self.proc)

class jemalloc_chunks(gdb.Command):
    '''Dump info on all available chunks'''

    def __init__(self):
        gdb.Command.__init__(self, 'jechunks', gdb.COMMAND_OBSCURE)
       
        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        unmask_jemalloc.dump_chunks(proc = self.proc)

class jemalloc_arenas(gdb.Command):
    '''Dump info on jemalloc arenas'''

    def __init__(self):
        gdb.Command.__init__(self, 'jearenas', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        unmask_jemalloc.dump_arenas(proc = self.proc)

class jemalloc_runs(gdb.Command):
    '''Dump info on jemalloc runs'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeruns', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        arg = arg.split()

        if len(arg) >= 1 and arg[0] == '-c':
            current_runs = true
        else:
            current_runs = false

        unmask_jemalloc.dump_runs(dump_current_runs = current_runs, \
                proc = self.proc)

class jemalloc_bins(gdb.Command):
    '''Dump info on jemalloc bins'''

    def __init__(self):
        gdb.Command.__init__(self, 'jebins', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
        unmask_jemalloc.dump_bins(proc = self.proc)

class jemalloc_regions(gdb.Command):
    '''Dump all current regions of the given size class'''

    def __init__(self):
        gdb.Command.__init__(self, 'jeregions', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):

        if arg == '':
            print('[unmask_jemalloc] usage: jeregions <size class>')
            print('[unmask_jemalloc] for example: jeregions 1024')
            return

        size_class = int(arg)
        unmask_jemalloc.dump_regions(size_class, proc = self.proc)

class jemalloc_search(gdb.Command):
    '''Search the jemalloc heap for the given hex value'''

    def __init__(self):
        gdb.Command.__init__(self, 'jesearch', gdb.COMMAND_OBSCURE)

        self.proc = gdb.inferiors()[0]

    def invoke(self, arg, from_tty):
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

        unmask_jemalloc.search(search_for, \
                search_current_runs = current_runs, proc = self.proc)

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
