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
      - directories:
        - /srv/graphite/whisper
    time_zone: Europe/Berlin

Config sections
```````````````

Default sections
^^^^^^^^^^^^^^^^

*search_index*

  The location of the search index used for searching metrics. Note that it
  needs to be writable by the graphite-api process.

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

*allowed_origins*

  Allows you to do cross-domain (CORS) requests to the Graphite API. Say you
  have a dashboard at ``dashboard.example.com`` that makes AJAX requests to
  ``graphite.example.com``, just set the value accordingly::

      allowed_origins:
        - dashboard.example.com

  You can specify as many origins as you want.

Custom location
---------------

If you need the Graphite-API config file to be stored in another place than
``/etc/graphite-api.yaml``, you can set a custom location using the
``GRAPHITE_API_CONFIG`` environment variable::

    export GRAPHITE_API_CONFIG=/var/lib/graphite/config.yaml
