De Mysteriis Dom jemalloc
=========================

A new version of the Firefox/jemalloc exploitation swiss army knife.

Overview of the new design:

<pre>

    +------------+
    | gdb_driver |
    +------------+
          ^
          |
          |
     +----------------+      +------+
     | unmask_jemalloc| <--- | util |
     +----------------+      +------+
          ^         ^
          |         |
      +----------+  |
      | jemalloc |  |
      +----------+  |
               ^    |
               |    |
         +------------+
         | gdb_engine |
         +------------+
               ^
               |
            +-----+
            | gdb |
            +-----+

</pre>
