Storage finders
---------------

Graphite-API searches and fetches metrics from time series databases using an
interface called *finders*. The default finder provided with Graphite-API is
the one that integrates with Whisper databases.

Customizing finders can be done in the ``finders`` section of the Graphite-API
configuration file:

.. code-block:: yaml

    finders:
      - graphite_api.finders.whisper.WhisperFinder

Several values are allowed, to let you store different kinds of metrics at
different places or smoothly handle transitions from one time series database
to another.

The default finder reads data from a Whisper database.

Custom finders
^^^^^^^^^^^^^^

``finders`` being a list of arbitrary python paths, it is relatively easy to
write a custom finder if you want to read data from other places than Whisper.
A finder is a python class with a ``find_nodes()`` method:

.. code-block:: python

    class CustomFinder(object):
        def find_nodes(self, query):
            # ...

``query`` is a ``FindQuery`` object. ``find_nodes()`` is the entry point when
browsing the metrics tree. It must yield leaf or branch nodes matching the
query:

.. code-block:: python

    from graphite_api.node import LeafNode, BranchNode

    class CustomFinder(object):
        def find_nodes(self, query):
            # find some paths matching the query, then yield them
            # is_branch or is_leaf are predicates you need to implement
            for path in matches:
                if is_branch(path):
                    yield BranchNode(path)
                if is_leaf(path):
                    yield LeafNode(path, CustomReader(path))


``LeafNode`` is created with a *reader*, which is the class responsible for
fetching the datapoints for the given path. It is a simple class with 2
methods: ``fetch()`` and ``get_intervals()``:

.. code-block:: python

    from graphite_api.intervals import IntervalSet, Interval

    class CustomReader(object):
        __slots__ = ('path',)  # __slots__ is recommended to save memory on readers

        def __init__(self, path):
            self.path = path

        def fetch(self, start_time, end_time):
            # fetch data
            time_info = _from_, _to_, _step_
            return time_info, series

        def get_intervals(self):
            return IntervalSet([Interval(start, end)])

``fetch()`` must return a list of 2 elements: the time info for the data and
the datapoints themselves. The time info is a list of 3 items: the start time
of the datapoints (in unix time), the end time and the time step (in seconds)
between the datapoints.

The datapoints is a list of points found in the database for the required
interval. There must be ``(end - start) / step`` points in the dataset even if
the database has gaps: gaps can be filled with ``None`` values.

``get_intervals()`` is a method that hints graphite-web about the time range
available for this given metric in the database. It must return an
``IntervalSet`` of one or more ``Interval`` objects.

Fetching multiple paths at once
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If your storage backend allows it, fetching multiple paths at once is useful
to avoid sequential fetches and save time and resources. This can be achieved
in three steps:

* Subclass ``LeafNode`` and add a ``__fetch_multi__`` class attribute to your
  subclass::

      class CustomLeafNode(LeafNode):
          __fetch_multi__ = 'custom'

  The string ``'custom'`` is used to identify backends and needs to be unique
  per-backend.

* Add the ``__fetch_multi__`` to your finder class::

      class CustomFinder(objects):
          __fetch_multi__ = 'custom'

* Implement a ``fetch_multi()`` method on your finder::

      class CustomFinder(objects):
          def fetch_multi(self, nodes, start_time, end_time):
              paths = [node.path for node in nodes]
              # fetch paths
              return time_info, series

  ``time_info`` is the same structure as the one returned by ``fetch()``.
  ``series`` is a dictionnary with paths as keys and datapoints as values.

Installing custom finders
^^^^^^^^^^^^^^^^^^^^^^^^^

In order for your custom finder to be importable, you need to package it under
a namespace of your choice. Python packaging won't be covered here but you can
look at third-party finders to get some inspiration:

* `Cyanite finder <https://github.com/brutasse/graphite-cyanite>`_

Configuration
^^^^^^^^^^^^^

Graphite-API instantiates finders and passes it its whole parsed configuration
file, as a Python data structure. External finders can require extra sections
in the configuration file to setup access to the time series database they
communicate with. For instance, let's say your ``CustomFinder`` needs two
configuration parameters, a host and a user:

.. code-block:: python

    class CustomFinder(object):
        def __init__(self, config):
            config.setdefault('custom', {})
            self.user = config['custom'].get('user', 'default')
            self.host = config['custom'].get('host', 'localhost')

The configuration file would look like:

.. code-block:: yaml

    finders:
      - custom.CustomFinder
    custom:
      user: myuser
      host: example.com

When possible, try to use sane defaults that would "just work" for most common
setups. Here if the ``custom`` section isn't provided, the finder uses
``default`` as user and ``localhost`` as host.
