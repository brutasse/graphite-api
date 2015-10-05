============
Installation
============

Debian / Ubuntu: native package
===============================

If you run Debian 8 or Ubuntu 14.04 LTS, you can use one of the available
packages which provides a self-contained build of graphite-api. Builds are
available on the `releases`_ page.

.. _releases: https://github.com/brutasse/graphite-api/releases

Once installed, Graphite-api should be running as a service and available on
port 8888. The package contains all the :ref:`optional dependencies <extras>`.

Python package
==============

Prerequisites
-------------

Installing Graphite-API requires:

* Python 2 (2.6 and above) or 3 (3.3 and above), with development files. On
  debian/ubuntu, you'll want to install ``python-dev``.

* ``gcc``. On debian/ubuntu, install ``build-essential``.

* Cairo, including development files. On debian/ubuntu, install the
  ``libcairo2-dev`` package.

* ``libffi`` with development files, ``libffi-dev`` on debian/ubuntu.

* Pip, the Python package manager. On debian/ubuntu, install ``python-pip``.

Global installation
-------------------

To install Graphite-API globally on your system, run as root::

    $ pip install graphite-api

Isolated installation (virtualenv)
----------------------------------

If you want to isolate Graphite-API from the system-wide python environment,
you can install it in a virtualenv.

::

    $ virtualenv /usr/share/python/graphite
    $ /usr/share/python/graphite/bin/pip install graphite-api

.. _extras:

Extra dependencies
------------------

When you install ``graphite-api``, all the dependencies for running a Graphite
server that uses Whisper as a storage backend are installed. You can specify
extra dependencies:

* For `Sentry`_ integration: ``pip install graphite-api[sentry]``.

* For `Cyanite`_ integration: ``pip install graphite-api[cyanite]``.

* For Cache support: ``pip install graphite-api[cache]``. You'll also need the
  driver for the type of caching you want to use (Redis, Memcache, etc.). See
  the `Flask-Cache docs`_ for supported cache types.


.. _Sentry: http://sentry.readthedocs.org/en/latest/
.. _Cyanite: https://github.com/brutasse/graphite-cyanite
.. _Flask-Cache docs: http://pythonhosted.org/Flask-Cache/#configuring-flask-cache

You can also combine several extra dependencies::

    $ pip install graphite-api[sentry,cyanite]
