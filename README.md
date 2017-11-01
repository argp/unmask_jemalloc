Development of unmask_jemalloc has stopped; please use [shadow](https://github.com/CENSUS/shadow/) instead!
===========================================================================================================

De Mysteriis Dom jemalloc
-------------------------

A new version of the Firefox/jemalloc exploitation swiss army knife.

Overview of the new design (read the arrow as "imports"):
  
    -------------------------------------------------------------------
                                     debugger-required frontend (glue)
     +------------+
     | gdb_driver |
     +------------+
          ^
          |
    ------+------------------------------------------------------------
          |                          core logic (debugger-agnostic)
          |
     +-----------------+      +------+
     | unmask_jemalloc | <--- | util |
     +-----------------+      +------+
          ^          ^           |
          |          |           |
      +----------+   |           |
      | jemalloc | <-+-----------|
      +----------+   |           |
               ^     |           |
               |     |           |
    -----------+-----+-----------+-------------------------------------
               |     |           |   debugger-depended APIs
         +------------+          |
         | gdb_engine | <--------+
         +------------+
           ^
           |
           |
    -------+-----------------------------------------------------------
           |                         debugger-provided backend
        +-----+
        | gdb |
        +-----+

    -------------------------------------------------------------------

The goal is, obviously, to have all debugger-depended code in the
*_driver and *_engine modules.

