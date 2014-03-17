import copy
import pytz
import time

from mock import patch, call, MagicMock

from graphite_api import functions
from graphite_api.app import app
from graphite_api.render.attime import parseATTime
from graphite_api.render.datalib import TimeSeries

from . import TestCase


def return_greater(series, value):
    return [i for i in series if i is not None and i > value]


def return_less(series, value):
    return [i for i in series if i is not None and i < value]


class FunctionsTest(TestCase):
    def test_highest_max(self):
        config = [20, 50, 30, 40]
        seriesList = [range(max_val) for max_val in config]

        # Expect the test results to be returned in decending order
        expected = [
            [seriesList[1]],
            [seriesList[1], seriesList[3]],
            [seriesList[1], seriesList[3], seriesList[2]],
            # Test where num_return == len(seriesList)
            [seriesList[1], seriesList[3], seriesList[2], seriesList[0]],
            # Test where num_return > len(seriesList)
            [seriesList[1], seriesList[3], seriesList[2], seriesList[0]],
        ]
        for index, test in enumerate(expected):
            results = functions.highestMax({}, seriesList, index + 1)
            self.assertEqual(test, results)

    def test_highest_max_empty_series_list(self):
        # Test the function works properly with an empty seriesList provided.
        self.assertEqual([], functions.highestMax({}, [], 1))

    def testGetPercentile(self):
        seriesList = [
            ([None, None, 15, 20, 35, 40, 50], 20),
            (range(100), 30),
            (range(200), 60),
            (range(300), 90),
            (range(1, 101), 31),
            (range(1, 201), 61),
            (range(1, 301), 91),
            (range(0, 102), 30),
            (range(1, 203), 61),
            (range(1, 303), 91),
        ]
        for index, conf in enumerate(seriesList):
            series, expected = conf
            result = functions._getPercentile(series, 30)
            self.assertEqual(
                expected, result,
                ('For series index <%s> the 30th percentile ordinal is not '
                 '%d, but %d ' % (index, expected, result)))

    def test_n_percentile(self):
        seriesList = []
        config = [
            [15, 35, 20, 40, 50],
            range(1, 101),
            range(1, 201),
            range(1, 301),
            range(0, 100),
            range(0, 200),
            range(0, 300),
            # Ensure None values in list has no effect.
            [None, None, None] + list(range(0, 300)),
        ]

        for i, c in enumerate(config):
            seriesList.append(TimeSeries('Test(%d)' % i, 0, 1, 1, c))

        def n_percentile(perc, expected):
            result = functions.nPercentile({}, seriesList, perc)
            self.assertEqual(expected, result)

        n_percentile(30, [[20], [31], [61], [91], [30], [60], [90], [90]])
        n_percentile(90, [[50], [91], [181], [271], [90], [180], [270], [270]])
        n_percentile(95, [[50], [96], [191], [286], [95], [190], [285], [285]])

    def test_sorting_by_total(self):
        seriesList = []
        config = [[1000, 100, 10, 0], [1000, 100, 10, 1]]
        for i, c in enumerate(config):
            seriesList.append(TimeSeries('Test(%d)' % i, 0, 0, 0, c))

        self.assertEqual(1110, functions.safeSum(seriesList[0]))

        result = functions.sortByTotal({}, seriesList)

        self.assertEqual(1111, functions.safeSum(result[0]))
        self.assertEqual(1110, functions.safeSum(result[1]))

    def _generate_series_list(self, config=(
        range(101),
        range(2, 103),
        [1] * 2 + [None] * 90 + [1] * 2 + [None] * 7
    )):
        seriesList = []

        now = int(time.time())

        for i, c in enumerate(config):
            name = "collectd.test-db{0}.load.value".format(i + 1)
            series = TimeSeries(name, now - 101, now, 1, c)
            series.pathExpression = name
            seriesList.append(series)
        return seriesList

    def test_remove_above_percentile(self):
        seriesList = self._generate_series_list()
        percent = 50
        results = functions.removeAbovePercentile({}, seriesList, percent)
        for result, exc in zip(results, [[], [51, 52]]):
            self.assertListEqual(return_greater(result, percent), exc)

    def test_remove_below_percentile(self):
        seriesList = self._generate_series_list()
        percent = 50
        results = functions.removeBelowPercentile({}, seriesList, percent)
        expected = [[], [], [1] * 4]

        for i, result in enumerate(results):
            self.assertListEqual(return_less(result, percent), expected[i])

    def test_remove_above_value(self):
        seriesList = self._generate_series_list()
        value = 5
        results = functions.removeAboveValue({}, seriesList, value)
        for result in results:
            self.assertListEqual(return_greater(result, value), [])

    def test_remove_below_value(self):
        seriesList = self._generate_series_list()
        value = 5
        results = functions.removeBelowValue({}, seriesList, value)
        for result in results:
            self.assertListEqual(return_less(result, value), [])

    def test_limit(self):
        seriesList = self._generate_series_list()
        limit = len(seriesList) - 1
        results = functions.limit({}, seriesList, limit)
        self.assertEqual(len(results), limit,
                         "More than {0} results returned".format(limit))

    def _verify_series_options(self, seriesList, name, value):
        """
        Verify a given option is set and True for each series in a
        series list
        """
        for series in seriesList:
            self.assertIn(name, series.options)
            if value is True:
                test_func = self.assertTrue
            else:
                test_func = self.assertEqual

            test_func(series.options.get(name), value)

    def test_second_y_axis(self):
        seriesList = self._generate_series_list()
        results = functions.secondYAxis({}, seriesList)
        self._verify_series_options(results, "secondYAxis", True)

    def test_draw_as_infinite(self):
        seriesList = self._generate_series_list()
        results = functions.drawAsInfinite({}, seriesList)
        self._verify_series_options(results, "drawAsInfinite", True)

    def test_line_width(self):
        seriesList = self._generate_series_list()
        width = 10
        results = functions.lineWidth({}, seriesList, width)
        self._verify_series_options(results, "lineWidth", width)

    def test_transform_null(self):
        seriesList = self._generate_series_list()
        transform = -5
        results = functions.transformNull({}, copy.deepcopy(seriesList),
                                          transform)

        for counter, series in enumerate(seriesList):
            if not None in series:
                continue
            # If the None values weren't transformed, there is a problem
            self.assertNotIn(None, results[counter],
                             "tranformNull should remove all None values")
            # Anywhere a None was in the original series, verify it
            # was transformed to the given value it should be.
            for i, value in enumerate(series):
                if value is None:
                    result_val = results[counter][i]
                    self.assertEqual(
                        transform, result_val,
                        "Transformed value should be {0}, not {1}".format(
                            transform, result_val))

    def test_alias(self):
        seriesList = self._generate_series_list()
        substitution = "Ni!"
        results = functions.alias({}, seriesList, substitution)
        for series in results:
            self.assertEqual(series.name, substitution)

    def test_alias_sub(self):
        seriesList = self._generate_series_list()
        substitution = "Shrubbery"
        results = functions.aliasSub({}, seriesList, "^\w+", substitution)
        for series in results:
            self.assertTrue(
                series.name.startswith(substitution),
                "aliasSub should replace the name with {0}".format(
                    substitution))

    # TODO: Add tests for * globbing and {} matching to this
    def test_alias_by_node(self):
        seriesList = self._generate_series_list()

        def verify_node_name(*nodes):
            # Use deepcopy so the original seriesList is unmodified
            results = functions.aliasByNode({}, copy.deepcopy(seriesList),
                                            *nodes)

            for i, series in enumerate(results):
                fragments = seriesList[i].name.split('.')
                # Super simplistic. Doesn't match {thing1,thing2}
                # or glob with *, both of what graphite allow you to use
                expected_name = '.'.join([fragments[i] for i in nodes])
                self.assertEqual(series.name, expected_name)

        verify_node_name(1)
        verify_node_name(1, 0)
        verify_node_name(-1, 0)

        # Verify broken input causes broken output
        with self.assertRaises(IndexError):
            verify_node_name(10000)

    def test_alpha(self):
        seriesList = self._generate_series_list()
        alpha = 0.5
        results = functions.alpha({}, seriesList, alpha)
        self._verify_series_options(results, "alpha", alpha)

    def test_color(self):
        seriesList = self._generate_series_list()
        color = "red"
        # Leave the original seriesList unmodified
        results = functions.color({}, copy.deepcopy(seriesList), color)

        for i, series in enumerate(results):
            self.assertTrue(
                hasattr(series, "color"),
                "The transformed seriesList is missing the 'color' attribute",
            )
            self.assertFalse(
                hasattr(seriesList[i], "color"),
                "The original seriesList shouldn't have a 'color' attribute",
            )
            self.assertEqual(series.color, color)

    def test_scale(self):
        seriesList = self._generate_series_list()
        multiplier = 2
        # Leave the original seriesList undisturbed for verification
        results = functions.scale({}, copy.deepcopy(seriesList), multiplier)
        for i, series in enumerate(results):
            for counter, value in enumerate(series):
                if value is None:
                    continue
                original_value = seriesList[i][counter]
                expected_value = original_value * multiplier
                self.assertEqual(value, expected_value)

    def test_average_series(self):
        series = self._generate_series_list()
        average = functions.averageSeries({}, series)[0]
        self.assertEqual(average[:3], [1.0, 5/3., 3.0])

    def test_average_series_wildcards(self):
        series = self._generate_series_list()
        average = functions.averageSeriesWithWildcards({}, series, 1)[0]
        self.assertEqual(average[:3], [1.0, 5/3., 3.0])
        self.assertEqual(average.name, 'collectd.load.value')

    def _generate_mr_series(self):
        seriesList = [
            TimeSeries('group.server1.metric1', 0, 1, 1, [None]),
            TimeSeries('group.server1.metric2', 0, 1, 1, [None]),
            TimeSeries('group.server2.metric1', 0, 1, 1, [None]),
            TimeSeries('group.server2.metric2', 0, 1, 1, [None]),
        ]
        mappedResult = [
            [seriesList[0], seriesList[1]],
            [seriesList[2], seriesList[3]]
        ]
        return seriesList, mappedResult

    def test_mapSeries(self):
        seriesList, expectedResult = self._generate_mr_series()
        results = functions.mapSeries({}, copy.deepcopy(seriesList), 1)
        self.assertEqual(results, expectedResult)

    def test_reduceSeries(self):
        sl, inputList = self._generate_mr_series()
        expectedResult = [
            TimeSeries('group.server1.reduce.mock', 0, 1, 1, [None]),
            TimeSeries('group.server2.reduce.mock', 0, 1, 1, [None])
        ]
        resultSeriesList = [TimeSeries('mock(series)', 0, 1, 1, [None])]
        mock = MagicMock(return_value=resultSeriesList)
        with patch.dict(app.config['GRAPHITE']['functions'], {'mock': mock}):
            results = functions.reduceSeries({}, copy.deepcopy(inputList),
                                             "mock", 2, "metric1", "metric2")
            self.assertEqual(results, expectedResult)
        self.assertEqual(mock.mock_calls, [call({}, inputList[0]),
                                           call({}, inputList[1])])

    def test_sum_series(self):
        series = self._generate_series_list()
        sum_ = functions.sumSeries({}, series)[0]
        self.assertEqual(sum_.pathExpression,
                         "sumSeries(collectd.test-db1.load.value,"
                         "collectd.test-db2.load.value,"
                         "collectd.test-db3.load.value)")
        self.assertEqual(sum_[:3], [3, 5, 6])

    def test_sum_series_wildcards(self):
        series = self._generate_series_list()
        sum_ = functions.sumSeriesWithWildcards({}, series, 1)[0]
        self.assertEqual(sum_.pathExpression,
                         "sumSeries(collectd.test-db3.load.value,"
                         "sumSeries(collectd.test-db1.load.value,"
                         "collectd.test-db2.load.value))")
        self.assertEqual(sum_[:3], [3, 5, 6])

    def test_diff_series(self):
        series = self._generate_series_list()[:2]
        diff = functions.diffSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(diff[:3], [-2, -2, -2])

    def test_stddev_series(self):
        series = self._generate_series_list()[:2]
        dev = functions.stddevSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(dev[:3], [1.0, 1.0, 1.0])

    def test_min_series(self):
        series = self._generate_series_list()[:2]
        min_ = functions.minSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(min_[:3], [0, 1, 2])

    def test_max_series(self):
        series = self._generate_series_list()[:2]
        max_ = functions.maxSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(max_[:3], [2, 3, 4])

    def test_range_of_series(self):
        series = self._generate_series_list()[:2]
        range_ = functions.rangeOfSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(range_[:3], [2, 2, 2])

    def test_percentile_of_series(self):
        series = self._generate_series_list()[:2]
        percent = functions.percentileOfSeries({}, series, 50)[0]
        self.assertEqual(percent[:3], [2, 3, 4])

        with self.assertRaises(ValueError):
            functions.percentileOfSeries({}, series, -1)

    def test_keep_last_value(self):
        series = self._generate_series_list()[2]
        last = functions.keepLastValue({}, [series], limit=97)[0]
        self.assertEqual(last[:3], [1, 1, 1])

        series[-1] = 1
        last = functions.keepLastValue({}, [series], limit=97)[0]
        self.assertEqual(last[:3], [1, 1, 1])

    def test_as_percent(self):
        series = self._generate_series_list()
        perc = functions.asPercent({}, series)[0]
        self.assertEqual(perc[:2], [0.0, 20.0])
        self.assertEqual(perc[3], 37.5)

        with self.assertRaises(ValueError):
            functions.asPercent({}, series[:2], [1, 2])

        perc = functions.asPercent({}, series[:2], [series[2]])[0]
        self.assertEqual(perc[:2], [0.0, 100.0])

        perc = functions.asPercent({}, series[:2], 12)[0]
        self.assertEqual(perc[:2], [0.0, 8.333333333333332])

    def test_divide_series(self):
        series = self._generate_series_list()
        div = functions.divideSeries({}, [series[0]], [series[1]])[0]
        self.assertEqual(div[:3], [0, 1/3., 0.5])

        with self.assertRaises(ValueError):
            functions.divideSeries({}, [series[0]], [1, 2])

    def test_multiply_series(self):
        series = self._generate_series_list()
        mul = functions.multiplySeries({}, series[:2])[0]
        self.assertEqual(mul[:3], [0, 3, 8])

        mul = functions.multiplySeries({}, series[:1])[0]
        self.assertEqual(mul[:3], [0, 1, 2])

    def test_weighted_average(self):
        series = self._generate_series_list()
        weight = functions.weightedAverage({}, [series[0]], [series[1]], 0)
        self.assertEqual(weight[:3], [0, 1, 2])

    def test_moving_median(self):
        series = self._generate_series_list()
        for s in series:
            self.write_series(s)
        tzinfo = pytz.timezone(app.config['TIME_ZONE'])
        median = functions.movingMedian({
            'startTime': parseATTime('-100s', tzinfo=tzinfo)
        }, series, '5s')[0]
        self.assertEqual(median[:4], [1, 0, 1, 1])

        median = functions.movingMedian({
            'startTime': parseATTime('-100s', tzinfo=tzinfo)
        }, series, 5)[0]
        self.assertEqual(median[:4], [1, 0, 1, 1])

    def test_invert(self):
        series = self._generate_series_list()
        invert = functions.invert({}, series)[0]
        self.assertEqual(invert[:5], [None, 1, 1/2., 1/3., 1/4.])

    def test_scale_to_seconds(self):
        series = self._generate_series_list()
        scaled = functions.scaleToSeconds({}, series, 10)[0]
        self.assertEqual(scaled[:3], [0, 10, 20])

    def test_absolute(self):
        series = self._generate_series_list(config=[range(-50, 50)])
        absolute = functions.absolute({}, series)[0]
        self.assertEqual(absolute[:3], [50, 49, 48])

    def test_offset(self):
        series = self._generate_series_list(config=[[None] + list(range(99))])
        offset = functions.offset({}, series, -50)[0]
        self.assertEqual(offset[:3], [None, -50, -49])

    def test_offset_to_zero(self):
        series = self._generate_series_list(
            config=[[None] + list(range(10, 110))])
        offset = functions.offsetToZero({}, series)[0]
        self.assertEqual(offset[:3], [None, 0, 1])

    def test_moving_average(self):
        series = self._generate_series_list()
        for s in series:
            self.write_series(s)
        tzinfo = pytz.timezone(app.config['TIME_ZONE'])
        average = functions.movingAverage({
            'startTime': parseATTime('-100s', tzinfo=tzinfo)
        }, series, '5s')[0]
        self.assertEqual(list(average)[:4], [0.5, 1/3., 0.5, 0.8])

        average = functions.movingAverage({
            'startTime': parseATTime('-100s', tzinfo=tzinfo)
        }, series, 5)[0]
        self.assertEqual(average[:4], [0.5, 1/3., 0.5, 0.8])

    def test_cumulative(self):
        series = self._generate_series_list(config=[range(100)])
        series[0].consolidate(2)
        cumul = functions.cumulative({}, series)[0]
        self.assertEqual(list(cumul)[:3], [1, 5, 9])

    def consolidate_by(self):
        series = self._generate_series_list(config=[range(100)])
        series[0].consolidate(2)
        min_ = functions.consolidateBy({}, series, 'min')
        self.assertEqual(list(min_)[:3], [0, 2, 4])

        max_ = functions.consolidateBy({}, series, 'max')
        self.assertEqual(list(max_)[:3], [1, 3, 5])

        avg_ = functions.consolidateBy({}, series, 'average')
        self.assertEqual(list(avg_)[:3], [0.5, 2.3, 4.5])

    def test_derivative(self):
        series = self._generate_series_list(config=[range(100)])
        der = functions.derivative({}, series)[0]
        self.assertEqual(der[:3], [None, 1, 1])

    def test_per_second(self):
        series = self._generate_series_list(config=[range(100)])
        series[0].step = 0.1
        per_sec = functions.perSecond({}, series)[0]
        self.assertEqual(per_sec[:3], [None, 10, 10])

        series = self._generate_series_list(config=[reversed(range(100))])
        series[0].step = 0.1
        per_sec = functions.perSecond({}, series, maxValue=20)[0]
        self.assertEqual(per_sec[:3], [None, None, None])

    def test_integral(self):
        series = self._generate_series_list(
            config=[list(range(1, 10)) * 9 + [None] * 10])
        integral = functions.integral({}, series)[0]
        self.assertEqual(integral[:3], [1, 3, 6])
        self.assertEqual(integral[-11:], [405] + [None] * 10)

    def test_non_negative_derivative(self):
        series = self._generate_series_list(config=[list(range(10)) * 10])
        der = functions.nonNegativeDerivative({}, series)[0]
        self.assertEqual(list(der),
                         [1 if i % 10 else None for i in range(100)])

        series = self._generate_series_list(
            config=[list(reversed(range(10))) * 10])
        der = functions.nonNegativeDerivative({}, series, maxValue=10)[0]
        self.assertEqual(list(der),
                         [None] + [10 if i % 10 else 9 for i in range(1, 100)])

    def test_stacked(self):
        series = self._generate_series_list(
            config=[[None] + list(range(99)), range(50, 150)])
        stacked = functions.stacked({}, series)[1]
        self.assertEqual(stacked[:3], [50, 51, 53])

        stacked = functions.stacked({'totalStack': {}}, series)[1]
        self.assertEqual(stacked[:3], [50, 51, 53])
        self.assertEqual(stacked.name, 'stacked(collectd.test-db2.load.value)')

        stacked = functions.stacked({}, series, 'tx')[1]
        self.assertEqual(stacked[:3], [50, 51, 53])
        self.assertEqual(stacked.name, series[1].name)
