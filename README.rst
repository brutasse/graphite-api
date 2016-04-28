Graphite-API
============

.. image:: https://travis-ci.org/brutasse/graphite-api.svg?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/brutasse/graphite-api

.. image:: https://img.shields.io/coveralls/brutasse/graphite-api/master.svg
   :alt: Coverage Status
   :target: https://coveralls.io/r/brutasse/graphite-api?branch=master

Graphite-web, without the interface. Just the rendering HTTP API.

This is a minimalistic API server that replicates the behavior of
Graphite-web. I removed everything I could and simplified as much code as
possible while keeping the basic functionality.

Implemented API calls:

* ``/metrics/find``
* ``/metrics/expand``
* ``/render``

No-ops:

* ``/dashboard/find``
* ``/dashboard/load/<name>``
* ``/events/get_data``

Additional API calls:

* ``/index`` (``POST`` or ``PUT`` only): rebuilds the search index by
  recursively querying the storage backends for available paths. Replaces
  graphite-web's ``build-index`` command-line script.

Difference from graphite-web
----------------------------

* Stateless. No need for a database.
* No Pickle rendering.
* No remote rendering.
* JSON data in request bodies is supported, additionally to form data and
  querystring parameters.
* Ceres integration will be as an external backend.
* Compatibility with python 2 and 3.
* Easy to install and configure.

Goals
-----

* Solid codebase. Strict flake8 compatibility, good test coverage.
* Ease of installation/use/configuration.
* Compatibility with the original Graphite-web API and 3rd-party dashboards.

Non-goals
---------

* Support for very old Python versions (Python 2.6 is still supported but
  maybe not for long).
* Built-in support for every metric storage system in the world. Whisper is
  included by default, other storages are added via 3rd-party backends.

Documentation
-------------

`On readthedocs.org`_ or in the ``docs/`` directory.

.. _On readthedocs.org: http://graphite-api.readthedocs.io/en/latest/

Hacking
-------

`Tox`_ is used to run the tests for all supported environments. To get started
from a fresh clone of the repository:

.. code-block:: bash

    pip install tox
    tox

.. _Tox: https://testrun.org/tox/
