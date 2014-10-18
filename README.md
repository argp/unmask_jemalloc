De Mysteriis Dom jemalloc
=========================

A new version of the Firefox/jemalloc exploitation swiss army knife.

Overview of the new design:

gdb_driver imports:
    unmask_jemalloc imports:
        jemalloc
        util
        gdb_engine

