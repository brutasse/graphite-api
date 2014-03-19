Built-in functions
==================

Functions are used to transform, combine, and perform computations on series
data. They are applied by manipulating the ``target`` parameters in the
:doc:`Render API <render>`.

Usage
-----

Most functions are applied to one series list. Functions with the
parameter ``*seriesLists`` can take an arbitrary number of series lists.
To pass multiple series lists to a function which only takes one, use the
:py:func:`group` function.

.. _list-of-functions:

List of functions
-----------------

.. automodule:: graphite_api.functions
   :members:
