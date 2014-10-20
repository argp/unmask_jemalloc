De Mysteriis Dom jemalloc
=========================

A new version of the Firefox/jemalloc exploitation swiss army knife.

Overview of the new design (read the arrow as "imports"):

    +------------+
    | gdb_driver |
    +------------+
          ^
          |
     +----------------+      +------+
     | unmask_jemalloc| <--- | util |
     +----------------+      +------+
          ^          ^           |
          |          |           |
      +----------+   |           |
      | jemalloc | <-+-----------|
      +----------+   |           |
               ^     |           |
               |     |           |
         +------------+          |
         | gdb_engine | <--------+
         +------------+
               ^
               |
            +-----+
            | gdb |
            +-----+

