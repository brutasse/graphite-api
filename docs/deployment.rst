Deployment
==========

There are several options available, depending on your setup.

Gunicorn + nginx
----------------

First, you need to install Gunicorn. The easiest way is to use ``pip``::

    $ pip install gunicorn

If you have installed Graphite-API in a virtualenv, install Gunicorn in the
same virtualenv::

    $ /usr/share/python/graphite/bin/pip install gunicorn

Next, create the script that will run Graphite-API using your process watcher
of choice.

*Upstart*

::

    description "Graphite-API server"
    start on runlevel [2345]
    stop on runlevel [!2345]

    respawn

    exec gunicorn -w2 graphite_api.app:app -b 0.0.0.0:8888

*Supervisor*

::

    [program:graphite-api]
    command = gunicorn -w2 graphite_api.app:app -b 0.0.0.0:8888
    autostart = true
    autorestart = true

.. note::

    If you have installed Graphite-API and Gunicorn in a virtualenv, you
    need to use the full path to Gunicorn. Instead of ``gunicorn``, use
    ``/usr/share/python/graphite/bin/gunicorn`` (assuming your virtualenv is
    at ``/usr/share/python/graphite``).

See the `Gunicorn docs`_ for configuration options and command-line flags.

.. _Gunicorn docs: http://docs.gunicorn.org/en/latest/

Finally, configure the nginx vhost:

.. code-block:: nginx

    # /etc/nginx/sites-available/graphite.conf

    upstream graphite {
        server 127.0.0.1:8888 fail_timeout=0;
    }

    server {
        server_name graph;
        listen 80 default;
        root /srv/www/graphite;

        location / {
            try_files $uri @graphite;
        }

        location @graphite {
            proxy_pass http://graphite;
        }
    }

Enable the vhost and restart nginx::

    $ ln -s /etc/nginx/sites-available/graphite.conf /etc/nginx/sites-enabled
    $ service nginx restart

Apache + mod_wsgi
-----------------

First, you need to install mod_wsgi.

See the `mod_wsgi InstallationInstructions`_ for installation instructions.

.. _mod_wsgi InstallationInstructions: https://code.google.com/p/modwsgi/wiki/InstallationInstructions

Then create the graphite-api.wsgi:

.. code-block:: bash

    # /var/www/wsgi-scripts/graphite-api.wsgi

    from graphite_api.app import app as application

Finally, configure the apache vhost:

.. code-block:: apache

    # /etc/httpd/conf.d/graphite.conf

    LoadModule wsgi_module modules/mod_wsgi.so

    WSGISocketPrefix /var/run/wsgi

    Listen 8013
    <VirtualHost *:8013>

        WSGIDaemonProcess graphite-api processes=5 threads=5 display-name='%{GROUP}' inactivity-timeout=120
        WSGIProcessGroup graphite-api
        WSGIApplicationGroup %{GLOBAL}
        WSGIImportScript /var/www/wsgi-scripts/graphite-api.wsgi process-group=graphite-api application-group=%{GLOBAL}

        WSGIScriptAlias / /var/www/wsgi-scripts/graphite-api.wsgi

        <Directory /var/www/wsgi-scripts/>
            Order deny,allow
            Allow from all
        </Directory>
	</VirtualHost>

Adapt the mod_wsgi configuration to your requirements.

See the `mod_wsgi QuickConfigurationGuide`_ for an overview of configurations and `mod_wsgi ConfigurationDirectives`_ to see all configuration directives

.. _mod_wsgi QuickConfigurationGuide: https://code.google.com/p/modwsgi/wiki/QuickConfigurationGuide

.. _mod_wsgi ConfigurationDirectives: https://code.google.com/p/modwsgi/wiki/ConfigurationDirectives

Restart apache::

    $ service httpd restart

Docker
------

Create a ``graphite-api.yaml`` configuration file with your desired config.

Create a ``Dockerfile``::

    FROM brutasse/graphite-api

Build your container::

    docker build -t graphite-api .

Run it::

    docker run -t -i -p 8888:8888 graphite-api

``/srv/graphite`` is a docker ``VOLUME``. You can use that to provide whisper
data from the host (or from another docker container) to the graphite-api
container::

    docker run -t -i -v /path/to/graphite:/srv/graphite -p 8888:8888 graphite-api

This container has all the :ref:`extra packages <extras>` included. Cyanite
backend and Sentry integration are available.

Nginx + uWSGI
-------------

First, you need to install uWSGI with Python support. On Debian, install ``uwsgi-plugin-python``.

Then create the uWSGI file for Graphite-API in
``/etc/uwsgi/apps-available/graphite-api.ini``:

.. code-block:: ini

    [uwsgi]
    processes = 2
    socket = localhost:8080
    plugins = python27
    module = graphite_api.app:app

If you installed Graphite-API in a virtualenv, specify the virtualenv path:

.. code-block:: ini

    home = /var/www/wsgi-scripts/env

If you need a custom location for Graphite-API's config file, set the
environment variable like this:

.. code-block:: ini

    env = GRAPHITE_API_CONFIG=/var/www/wsgi-scripts/config.yml

Enable ``graphite-api.ini`` and restart uWSGI:

.. code-block:: bash

    $ ln -s /etc/uwsgi/apps-available/graphite-api.ini /etc/uwsgi/apps-enabled
    $ service uwsgi restart

Finally, configure the nginx vhost:

.. code-block:: nginx

    # /etc/nginx/sites-available/graphite.conf

    server {
        listen 80;

        location / {
            include uwsgi_params;
            uwsgi_pass localhost:8080;
        }
    }

Enable the vhost and restart nginx:

.. code-block:: bash

    $ ln -s /etc/nginx/sites-available/graphite.conf /etc/nginx/sites-enabled
    $ service nginx restart

Other deployment methods
------------------------

They currently aren't described here but there are several other ways to serve
Graphite-API:

* nginx + circus + chaussette

If you feel like contributing some documentation, feel free to open pull a
request on the `Graphite-API repository`_.

.. _Graphite-API repository: https://github.com/brutasse/graphite-api
