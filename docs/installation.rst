============
Installation
============

Debian / Ubuntu: native package
===============================

If you run Debian 7 or Ubuntu 14.04 LTS, you can use `exoscale`_'s `community
repository`_ which provides a self-contained build of graphite-api.

.. _exoscale: https://www.exoscale.ch
.. _community repository: https://packagecloud.io/exoscale/community

First, add packagecloud's APT key::

    curl https://packagecloud.io/gpg.key | sudo apt-key add -

Then, create ``/etc/apt/sources.list.d/exoscale_community.list`` with the
following content.

On Debian (Wheezy)::

    deb https://packagecloud.io/exoscale/community/debian/ wheezy main

On Ubuntu (14.04 LTS)::

    deb https://packagecloud.io/exoscale/community/ubuntu/ trusty main

Then run::

    sudo apt-get update
    sudo apt-get install graphite-api

Graphite-api should be running as a service and available on port 8888. The
package contains all the :ref:`optional dependencies <extras>`.

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


.. _Sentry: http://sentry.readthedocs.org/en/latest/
.. _Cyanite: https://github.com/brutasse/graphite-cyanite

You can also combine several extra dependencies::

    $ pip install graphite-api[sentry,cyanite]
