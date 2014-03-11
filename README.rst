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

Additional API calls:

* ``/index`` (``POST`` or ``PUT`` only): rebuilds the search index by
  recursively querying the storage backends for available paths. Replaces
  graphite-web's ``build-index`` command-line script.

Difference from graphite-web
----------------------------

* Stateless. No need for a database.
* No caching. Rendering is live.
* No Pickle.
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

Installation
------------

.. code-block:: bash

    git clone https://github.com/brutasse/graphite-api.git
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

Storage finders
```````````````

Graphite-API can read from any metrics store as long as it has a compatible
storage finder. Finders can be configured this way:

.. code-block:: yaml

    finders:
      - graphite_api.finders.whisper.WhisperFinder
      - cyanite.CyaniteFinder

Multiple finders are allowed.

Functions
`````````

Custom functions can be added to extend the built-in grammar. The default
functions are:

.. code-block:: yaml

    functions:
      - graphite_api.functions.SeriesFunctions
      - graphite_api.functions.PieFunctions

CORS
````

If your dashboard and your graphite-api server don't have the same hostname,
you might need to setup CORS to allow browsers to make cross-domain HTTP
requests.

For example, if you have graphite-api on ``https://api.graph.example.com`` and
grafana on ``https://dashboard.graph.example.com``, you need the following in
your graphite-api config:

.. code-block:: yaml

    allowed_origins:
      - dashboard.graph.example.com

You can add as many hosts as you want.

Error handling
``````````````

Request exceptions can be sent to `Sentry`_ for painless debugging.

.. _Sentry: http://sentry.readthedocs.org/en/latest/

Just add to your config:

.. code-block:: yaml

    sentry_dsn: https://key:secret@host/id

And install *raven*, the sentry client::

    pip install raven[flask]

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

.. _Tox: https://testrun.org/tox/
