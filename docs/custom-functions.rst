Custom functions
================

Just like with storage finders, it is possible to extend Graphite-API to add
custom processing functions.

To give an example, let's implement a function that reverses the time series,
placing old values at the end and recent values at the beginning.

.. code-block:: python

    # reverse.py

    def reverseSeries(requestContex, seriesList):
        reverse = []
        for series in seriesList:
            reverse.append(TimeSeries(series.name, series.start, series.end,
                                      series.step, series[::-1]))
        return reverse

The first argument, ``requestContext``, holds some information about the
request parameters. ``seriesList`` is the list of paths found for the request
target.

Once you've created your function, declare it in a dictionnary:

.. code-block:: python

    ReverseFunctions = {
        'reverseSeries': reverseSeries,
    }

Add your module to the Graphite-API Python path and add it to the
configuration:

.. code-block:: yaml

    functions:
      - graphite_api.functions.SeriesFunctions
      - graphite_api.functions.PieFunctions
      - reverse.ReverseFunctions
