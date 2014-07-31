Configuration
=============

/etc/graphite-api.yaml
----------------------

The configuration file for Graphite-API lives at ``/etc/graphite-api.yaml``
and uses the YAML format. Creating the configuration file is optional: if
Graphite-API doesn't find the file, sane defaults are used. They are described
below.
You can also set a custom location using the
``GRAPHITE_API_CONFIG`` environment variable::

    export GRAPHITE_API_CONFIG=/var/lib/graphite/config.yaml

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
    time_zone: Europe/Berlin

Config sections
```````````````

Default sections
^^^^^^^^^^^^^^^^

*search_index*

  The location of the search index used for searching metrics. Note that it
  needs to be a file that is writable by the graphite-api process.

*finders*

  A list of python paths to the storage finders you want to use when fetching
  metrics.

*functions*

  A list of python paths to function definitions for transforming / analyzing
  time series data.

*time_zone*

  The time zone to use when generating graphs.

Extra sections
^^^^^^^^^^^^^^

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

*cache*
  Attaches a cache object to the application, using `Flask-Cache`_.
  Currently, it is not yet used for caching of http responses or internal
  data.  However, this can be useful for certain
  backends like `Graphite-Influxdb`_.
  The options are simply the same options as Flask-Cache expects.

  Example::

      cache:
          CACHE_TYPE: 'memcached'
          CACHE_KEY_PREFIX: 'graphite_api'

  .. note::

        This requires flask-cache and potentially other modules depending on which backend you choose.
        See the Flask-Cache docs.

            $ pip install Flask-Cache

.. _Flask-Cache: http://pythonhosted.org/Flask-Cache/
.. _Graphite-Influxdb: https://github.com/vimeo/graphite-influxdb

*statsd*
  Attaches a statsd object to the application, which can be used for
  instrumentation. Currently graphite-api itself doesn't use this,
  but some backends do, like `Graphite-Influxdb`_.

  Example::

      statsd:
          host: 'statsd_host'
          port: 8125  # not needed if default

  .. note::

        This requires the statsd module.

            $ pip install statsd

.. _Graphite-Influxdb: https://github.com/vimeo/graphite-influxdb

*allowed_origins*

  Allows you to do cross-domain (CORS) requests to the Graphite API. Say you
  have a dashboard at ``dashboard.example.com`` that makes AJAX requests to
  ``graphite.example.com``, just set the value accordingly::

      allowed_origins:
        - dashboard.example.com

  You can specify as many origins as you want.


/etc/graphTemplates.conf
------------------------
The configuration file for templates lives at ``/etc/graphTemplates.conf``
and uses the ini format like Graphite. Creating the configuration file is optional: if
Graphite-API doesn't find the file, sane defaults are used.

You can also set a custom location using the
``GRAPHITE_API_TEMPLATES_CONFIG`` environment variable::

    export GRAPHITE_API_TEMPLATES_CONFIG=/var/lib/graphite/graphTemplates.conf
