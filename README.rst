Graphite-API
============

Graphite-web, without the interface. Just the rendering HTTP API.

Fork of ``graphite-api`` specifically for use with an `InfluxDB backend <https://github.com/InfluxGraph/influxgraph>`_.

This is a minimalistic API server that replicates the behavior of
Graphite-web.

Implemented API calls:

* ``/metrics/find``
* ``/metrics/expand``
* ``/render``

No-ops:

* ``/dashboard/find``
* ``/dashboard/load/<name>``
* ``/events/get_data``

Changes from graphite-api
---------------------------

* Hardcoded `average` consolidation of all data points removed - consolidation handled by storage back-end.
* Cairo optional dependency - Json/raw formats by default.
* Hardcoded legacy whisper *index* file requirement removed. (``/srv/index``)
* ``maxdatapoints`` render query parameter removed - handled by storage back-end.
* Whisper hardcoded default configuration removed.
* Various fixes from pending graphite-api pull requests and back-ported fixes from graphite-web, ``asPercent`` among others.
* Performance improvements.


Difference from graphite-web
----------------------------

* Stateless. No need for a database.
* No Pickle rendering.
* No remote rendering.
* JSON data in request bodies is supported, additionally to form data and
  querystring parameters.
* Compatibility with python 2 and 3.
* Easy to install and configure.

Goals
-----

* Solid codebase. Strict flake8 compatibility, good test coverage.
* Ease of installation/use/configuration.
* Compatibility with the original Graphite-web API and 3rd-party dashboards.

Non-goals
---------

* Support for Python versions older than ``2.7``.
* Built-in support for every metric storage system in the world. Whisper is
  included by default, other storages are added via 3rd-party backends.

Documentation
-------------

`On readthedocs.org`_ or in the ``docs/`` directory.

.. _On readthedocs.org: https://graphite-api.readthedocs.io/en/latest/

CairoCFFI dependency
---------------------

Cairo is used to render graphs server side when target format is an image. By default, only Json and raw format outputs are enabled. Attempts to render image formats without Cairo will result in an error message that it is not installed.

It can be pulled in via extras - ``pip install influxgraph-graphite-api[cairo]``.

Hacking
-------

`Tox`_ is used to run the tests for all supported environments. To get started
from a fresh clone of the repository:

.. code-block:: bash

    pip install tox
    tox

.. _Tox: https://testrun.org/tox/
