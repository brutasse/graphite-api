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

    exec gunicorn -w2 graphite_api.app:app

*Supervisor*

::

    [program:graphite-api]
    command = gunicorn -w2 graphite_api.app:app
    autostart = true
    autorestart = true

.. note::

    If you have installed Graphite-API and Gunicorn in a virtualenv, you
    need to use the full path to Gunicorn. Instead of ``gunicorn``, use
    ``/usr/share/python/graphite/bin/gunicorn`` (assuming your virtualenv is
    at ``/usr/share/python/graphite``).

By default, Gunicorn serves Graphite-API on ``127.0.0.1:8000``. See the
`Gunicorn docs`_ for configuration options.

.. _Gunicorn docs: http://docs.gunicorn.org/en/latest/

Finally, configure the nginx vhost:

.. code-block:: nginx

    # /etc/nginx/sites-available/graphite.conf

    upstream graphite {
        server 127.0.0.1:8000 fail_timeout=0;
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

Docker
------

Create a ``graphite-api.yaml`` configuration file with your desired config.

Create a ``Dockerfile``::

    FROM brutasse/graphite-api

Build your container::

    docker build -t graphite-api .

Run it::

    docker run -t -i -p 8000:8000 graphite-api

``/srv/graphite`` is a docker ``VOLUME``. You can use that to provide whisper
data from the host (or from another docker container) to the graphite-api
container::

    docker run -t -i -v /path/to/graphite:/srv/graphite -p 8000:8000 graphite-api

This container has all the :ref:`extra packages <extras>` included. Cyanite
backend and Sentry integration are available.

Other deployment methods
------------------------

They currently aren't described here but there are several other ways to serve
Graphite-API:

* Apache + ``mod_wsgi``

* nginx + uwsgi

* nginx + circus + chaussette

If you feel like contributing some documentation, feel free to open pull a
request on the `Graphite-API repository`_.

.. _Graphite-API repository: https://github.com/brutasse/graphite-api
