De Mysteriis Dom jemalloc
=========================

A new version of the Firefox/jemalloc exploitation swiss army knife.

Overview of the new design (read the arrow as "imports"):
  
    ---------------------------------------------------------------
                                   debugger-required frontend
     +------------+
     | gdb_driver |
     +------------+
          ^
          |
    ------+--------------------------------------------------------
          |                        core logic (debugger-agnostic)                         
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
    -----------+-----+-----------+---------------------------------
               |     |           | debugger engine implementation
         +------------+          |
         | gdb_engine | <--------+
         +------------+
           ^
           |
           |
    -------+-------------------------------------------------------
           |                       debugger-provided backend
        +-----+
        | gdb |
        +-----+

    ---------------------------------------------------------------

The goal is, obviously, to have all debugger-depended code in the
*_driver and *_engine modules.

