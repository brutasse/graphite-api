Graphite-API
============

.. image:: https://travis-ci.org/brutasse/graphite-api.png?branch=master
   :alt: Build Status
   :target: https://travis-ci.org/brutasse/graphite-api

.. image:: https://coveralls.io/repos/brutasse/graphite-api/badge.png?branch=master
   :alt: Coverage Status
   :target: https://coveralls.io/r/brutasse/graphite-api?branch=master

Graphite-web, without the interface. Just the rendering HTTP API.

This is a minimalistic API server that replicates the behavior of
Graphite-web. I removed everything I could and simplified as much code as
possible while keeping the basic functionality.

Implemented API calls:

* ``/metrics/find``
* ``/metrics/expand``
* ``/metrics/search`` (removed strange ``keep_query_pattern`` parameter)
* ``/render``

No-ops:

* ``/dashboard/find``
* ``/dashboard/load/<name>``
* ``/events/get_data``

Difference from graphite-web
----------------------------

* Stateless. No need for a database.
* No caching. Rendering is live.
* No Pickle.
* Graphite-web has a history of accepting URLs with or without a trailing
  slash. Graphite-API only supports URLs with no trailing slash.
* JSON data in request bodies is supported, additionally to form data and
  querystring parameters.
* Ceres integration will be as an external backend.
* Compatibility python 2 and 3.
* Easy to install and configure.

Goals
-----

* Solid codebase. Strict flake8 compatibility, good test coverage.
* Ease of installation/use/configuration.
* Compatibility with the original Graphite-web API.

Non-goals
---------

* Support for very old Python versions.
* Built-in support for every metric storage system in the world. Whisper is
  included by default, other storages are added via 3rd-party backends.

Installation
------------

.. code-block:: bash

    git clone git@github.com:brutasse/graphite-api.git
    cd graphite-api
    sudo python setup.py install

Alternatively, you can run ``setup.py install`` as a normal user, in a
virtualenv.

Configuration
-------------

The default config file path is ``/etc/graphite-api.conf``. The format is
YAML.

.. code-block:: yaml

    search_index: /srv/graphite/index
    whisper:
      directories:
        - /srv/graphite/whisper
    time_zone: Europe/Berlin

If you need the configuration file to be at a different location, you can set
the ``GRAPHITE_API_CONFIG`` environment variable to the location you want.

Deploying
---------

With `Gunicorn`_ or any WSGI server. The WSGI application is located at
``graphite_api.app:app``.

.. _Gunicorn: http://gunicorn.org/

.. code-block:: bash

    sudo pip install gunicorn
    gunicorn graphite_api.app:app

Hacking
-------

`Tox`_ is used to run the tests for all supported environments. To get started
from a fresh clone of the repository:

.. code-block:: bash

    pip install tox
    tox
