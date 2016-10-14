from graphite_api.render.datalib import TimeSeries, nonempty

from . import TestCase


class TimeSeriesTest(TestCase):
    def test_TimeSeries_init_no_args(self):
        with self.assertRaises(TypeError):
            TimeSeries()

    def test_TimeSeries_init_string_values(self):
        series = TimeSeries("collectd.test-db.load.value",
                            0, 2, 1, "ab")
        expected = TimeSeries("collectd.test-db.load.value",
                              0, 2, 1, ["a", "b"])
        self.assertEqual(series, expected)

    def test_TimeSeries_equal_list(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values), 1, values)
        with self.assertRaises(AssertionError):
            self.assertEqual(values, series)

    def test_TimeSeries_equal_list_color(self):
        values = range(0, 100)
        series1 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series1.color = 'white'
        series2 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series2.color = 'white'
        self.assertEqual(series1, series2)

    def test_TimeSeries_equal_list_color_bad(self):
        values = range(0, 100)
        series1 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series2 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series2.color = 'white'
        with self.assertRaises(AssertionError):
            self.assertEqual(series1, series2)

    def test_TimeSeries_equal_list_color_bad2(self):
        values = range(0, 100)
        series1 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series2 = TimeSeries("collectd.test-db.load.value",
                             0, len(values), 1, values)
        series1.color = 'white'
        with self.assertRaises(AssertionError):
            self.assertEqual(series1, series2)

    def test_TimeSeries_consolidate(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values)/2, 1, values)
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)

    def test_TimeSeries_iterate(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values), 1, values)
        for i, val in enumerate(series):
            self.assertEqual(val, values[i])

    def test_TimeSeries_iterate_valuesPerPoint_2_none_values(self):
        values = [None, None, None, None, None]
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values)/2, 1, values)
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        expected = TimeSeries("collectd.test-db.load.value",
                              0, 5, 1, [None, None, None])
        self.assertEqual(list(series), list(expected))

    def test_TimeSeries_iterate_valuesPerPoint_2_avg(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values)/2, 1, values)
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        expected = TimeSeries("collectd.test-db.load.value", 0, 5, 1,
                              list(map(lambda x: x+0.5, range(0, 100, 2))) +
                              [None])
        self.assertEqual(list(series), list(expected))

    def test_TimeSeries_iterate_valuesPerPoint_2_sum(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, 5, 1, values, consolidate='sum')
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        expected = TimeSeries("collectd.test-db.load.value",
                              0, 5, 1, list(range(1, 200, 4)) + [None])
        self.assertEqual(list(series), list(expected))

    def test_TimeSeries_iterate_valuesPerPoint_2_max(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, 5, 1, values, consolidate='max')
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        expected = TimeSeries("collectd.test-db.load.value",
                              0, 5, 1, list(range(1, 100, 2)) + [None])
        self.assertEqual(list(series), list(expected))

    def test_TimeSeries_iterate_valuesPerPoint_2_min(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, 5, 1, values, consolidate='min')
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        expected = TimeSeries("collectd.test-db.load.value",
                              0, 5, 1, list(range(0, 100, 2)) + [None])
        self.assertEqual(list(series), list(expected))

    def test_TimeSeries_iterate_valuesPerPoint_2_invalid(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, 5, 1, values, consolidate='bogus')
        self.assertEqual(series.valuesPerPoint, 1)
        series.consolidate(2)
        self.assertEqual(series.valuesPerPoint, 2)
        with self.assertRaises(Exception):
            list(series)


class DatalibFunctionTest(TestCase):
    def test_nonempty_true(self):
        values = range(0, 100)
        series = TimeSeries("collectd.test-db.load.value",
                            0, len(values), 1, values)
        self.assertTrue(nonempty(series))

    def test_nonempty_false_empty(self):
        series = TimeSeries("collectd.test-db.load.value", 0, 1, 1, [])
        self.assertFalse(nonempty(series))

    def test_nonempty_false_nones(self):
        series = TimeSeries("collectd.test-db.load.value",
                            0, 4, 1, [None, None, None, None])
        self.assertFalse(nonempty(series))
