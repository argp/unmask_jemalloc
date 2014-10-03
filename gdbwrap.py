# unmask_jemalloc - De Mysteriis Dom jemalloc
# 
# Copyright (c) 2014 Patroklos Argyroudis <argp at domain census-labs.com>
# Copyright (c) 2014 Chariton Karamitas <huku at domain census-labs.com>
# Copyright (c) 2014 Census, Inc. (http://www.census-labs.com/)

import sys

try:
    import gdb
except ImportError:
    print('[unmask_jemalloc] error: only usable from within gdb')
    sys.exit()

# EOF
