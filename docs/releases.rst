Graphite-API releases
=====================

1.0.2 -- **in development**
---------------------------

* Add CarbonLink support.

* Add support for configuring a cache backend and the ``noCache`` and
  ``cacheTimeout`` API options.

* When no timezone is provided in the configuration file, try to guess from
  the system's timezone with a fallback to UTC.

* Now supporting Flask >= 0.8 and Pyparsing >= 1.5.7.

* Add support for ``fetch_multi()`` in storage finders. This is useful for
  database-backed finders such as Cyanite because it allows fetching all time
  series at once instead of sequentially.

* Add ``multiplySeriesWithWildcards``, ``minimumBelow``, ``changed``,
  ``timeSlice`` and ``removeEmptySeries`` functions.

* Add optional ``step`` argument to ``time``, ``sin`` and ``randomWalk``
  functions.

* Add ``/metrics`` API call as an alias to ``/metrics/find``.

* Add missing ``/metrics/index.json`` API call.

* Allow wildcards origins (``*``) in CORS configuration.

* Whisper finder now logs debug information.

* Fix parsing dates such as "feb27" during month days > 28.

* Change ``sum()`` to return ``null`` instead of 0 when all series' datapoints
  are null at the same time. This is graphite-web's behavior.

* Extract paths of all targets before fetching data. This is a significant
  optimization for storage backends such as Cyanite that allow bulk-fetching
  metrics.

* Add JSONP support to all API endpoints that can return JSON.

* Fix 500 error when generating a SVG graph without any data.

* Fixes for the following graphite-web issues:

  * `#639 <https://github.com/graphite-project/graphite-web/issues/639>`_ --
    proper timezone handling of ``from`` and ``until`` with client-supplied
    timezones.
  * `#540 <https://github.com/graphite-project/graphite-web/issues/540>`_ --
    provide the last data point when rendering to JSON format.
  * `#381 <https://github.com/graphite-project/graphite-web/issues/381>`_ --
    make ``areaBetween()`` work either when passed 2 arguments or a single
    wildcard series of length 2.
  * `#702 <https://github.com/graphite-project/graphite-web/pull/702>`_ --
    handle backslash as path separator on windows.
  * `#410 <https://github.com/graphite-project/graphite-web/pull/410>`_ -- SVG
    output sometimes had an extra ``</g>`` tag.

1.0.1 -- 2014-03-21
-------------------

* ``time_zone`` set to UTC by default instead of Europe/Berlin.
* Properly log app exceptions.
* Fix constantLine for python 3.
* Create whisper directories if they don't exist.
* Fixes for the following graphite-web issues:

  * `#645 <https://github.com/graphite-project/graphite-web/pull/645>`_, `#625
    <https://github.com/graphite-project/graphite-web/issues/625>`_ -- allow
    ``constantLine`` to work even if there are no other targets in the graph.

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

* Fixes for the following graphite-web issues:

  * (meta) `#647 <https://github.com/graphite-project/graphite-web/issues/647>`_
    -- strip out the API from graphite-web.
  * `#665 <https://github.com/graphite-project/graphite-web/pull/665>`_ --
    address some DeprecationWarnings.
  * `#658 <https://github.com/graphite-project/graphite-web/issues/658>`_ --
    accept a float value in ``maxDataPoints``.
  * `#654 <https://github.com/graphite-project/graphite-web/pull/654>`_ --
    ignore invalid ``logBase`` values (<=1).
  * `#591 <https://github.com/graphite-project/graphite-web/issues/591>`_ --
    accept JSON data additionaly to querystring params or form data.
