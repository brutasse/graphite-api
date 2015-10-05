Configuration
=============

/etc/graphite-api.yaml
----------------------

The configuration file for Graphite-API lives at ``/etc/graphite-api.yaml``
and uses the YAML format. Creating the configuration file is optional: if
Graphite-API doesn't find the file, sane defaults are used. They are described
below.

Default values
``````````````

.. code-block:: yaml

    search_index: /srv/graphite/index
    finders:
      - graphite_api.finders.whisper.WhisperFinder
    functions:
      - graphite_api.functions.SeriesFunctions
      - graphite_api.functions.PieFunctions
    whisper:
      directories:
        - /srv/graphite/whisper
    time_zone: <system timezone> or UTC

Config sections
```````````````

Default sections
^^^^^^^^^^^^^^^^

*search_index*

  The location of the search index used for searching metrics. Note that it
  needs to be a file that is writable by the Graphite-API process.

*finders*

  A list of python paths to the storage finders you want to use when fetching
  metrics.

*functions*

  A list of python paths to function definitions for transforming / analyzing
  time series data.

*whisper*

  The configuration information for whisper. Only relevant when using
  WhisperFinder. Simply holds a ``directories`` key listing all directories
  containing whisper data.

*time_zone*

  The time zone to use when generating graphs. By default, Graphite-API tries
  to detect your system timezone. If detection fails it falls back to UTC. You
  can also manually override it if you want another value than your system's
  timezone.

Extra sections
^^^^^^^^^^^^^^

*carbon*

  Configuration information for reading data from carbon's cache. Items:

  *hosts*
    List of carbon-cache hosts, in the format ``hostname:port[:instance]``.

  *timeout*
    Socket timeout for carbon connections, in seconds.

  *retry_delay*
    Time to wait before trying to re-establish a failed carbon connection, in
    seconds.

  *hashing_keyfunc*
    Python path to a hashing function for metrics. If you use Carbon with
    consistent hashing and a custom function, you need to point to the same
    hashing function.

  *carbon_prefix*
    Prefix for carbon's internal metrics. When querying metrics starting with
    this prefix, requests are made to all carbon-cache instances instead of
    one instance selected by the key function. Default: ``carbon``.

  *replication_factor*
     The replication factor of your carbon setup. Default: ``1``.

  Example:

  .. code-block:: yaml

      carbon:
        hosts:
          - 127.0.0.1:7002
        timeout: 1
        retry_delay: 15
        carbon_prefix: carbon
        replication_factor: 1

*sentry_dsn*

  This is useful if you want to send Graphite-API's exceptions to a `Sentry`_
  instance for easier debugging.

  Example::

      sentry_dsn: https://key:secret@app.getsentry.com/12345

  .. note::

      Sentry integration requires Graphite-API to be installed with the
      corresponding extra dependency::

          $ pip install graphite-api[sentry]

.. _Sentry: http://sentry.readthedocs.org/en/latest/

*allowed_origins*

  Allows you to do cross-domain (CORS) requests to the Graphite API. Say you
  have a dashboard at ``dashboard.example.com`` that makes AJAX requests to
  ``graphite.example.com``, just set the value accordingly::

      allowed_origins:
        - dashboard.example.com

  You can specify as many origins as you want. A wildcard can be used to allow
  all origins::

      allowed_origins:
        - *

*cache*

  Lets you configure a cache for graph rendering. This is done via
  `Flask-Cache <http://pythonhosted.org/Flask-Cache/>`_ which supports a
  number of backends including memcache, Redis, filesystem or in-memory
  caching.

  Cache configuration maps directly to Flask-Cache's config values. For each
  ``CACHE_*`` config value, set the lowercased name in the ``cache`` section,
  without the prefix. Example::

      cache:
        type: redis
        redis_host: localhost

  This would configure Flask-Cache with ``CACHE_TYPE = 'redis'`` and
  ``CACHE_REDIS_HOST = 'localhost'``.

  Some cache options have default values defined by Graphite-API:

  * ``default_timeout``: 60

  * ``key_prefix``: ``'graphite-api:``.

  .. note::

      Caching functionality requires you to install the cache extra dependency
      but also the underlying driver. E.g. for redis, you'll need::

          $ pip install graphite-api[cache] redis

*statsd*

  Attaches a statsd object to the application, which can be used for
  instrumentation. Currently Graphite-API itself doesn't use this,
  but some backends do, like `Graphite-Influxdb`_.

  Example::

      statsd:
          host: 'statsd_host'
          port: 8125  # not needed if default

  .. note::

      This requires the statsd module::

          $ pip install statsd

.. _Graphite-Influxdb: https://github.com/vimeo/graphite-influxdb

*render_errors*

  If ``True`` (default), full tracebacks are returned in the HTTP
  response in case of application errors.

Custom location
---------------

If you need the Graphite-API config file to be stored in another place than
``/etc/graphite-api.yaml``, you can set a custom location using the
``GRAPHITE_API_CONFIG`` environment variable::

    export GRAPHITE_API_CONFIG=/var/lib/graphite/config.yaml
