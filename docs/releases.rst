Graphite-API releases
=====================

1.0.1 -- *not released yet!*
----------------------------

* ``time_zone`` set to UTC by default instead of Europe/Berlin.

1.0.0 -- 2014-03-20
-------------------

Version 1.0 is based on the master branch of Graphite-web, mid-March 2014,
with the following modifications:

* New ``/index`` API endpoint for re-building the index (replaces the
  build-index command-line script from graphite-web).

* Removal of memcache integration.

* Removal of Pickle integration.

* Removal of remote rendering.

* Support for Python 3.

* A lot more tests and test coverage.
