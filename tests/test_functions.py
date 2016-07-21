import copy
import math
import time

from datetime import datetime

import pytz

try:
    from unittest.mock import patch, call, MagicMock
except ImportError:
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

    # Test safeSum()
    def test_safe_sum_None(self):
        with self.assertRaises(TypeError):
            functions.safeSum(None)

    def test_safe_sum_empty_list(self):
        self.assertEqual(functions.safeSum([]), None)

    def test_safe_sum_all_numbers(self):
        self.assertEqual(functions.safeSum([1, 2, 3, 4]), 10)

    def test_safe_sum_all_None(self):
        self.assertEqual(functions.safeSum([None, None, None, None]), None)

    def test_safe_sum_mixed(self):
        self.assertEqual(functions.safeSum([10, None, 5, None]), 15)

    # Test safeDiff()
    def test_safe_diff_None(self):
        with self.assertRaises(TypeError):
            functions.safeDiff(None)

    def test_safe_diff_empty_list(self):
        self.assertEqual(functions.safeDiff([]), None)

    def test_safe_diff_all_numbers(self):
        self.assertEqual(functions.safeDiff([1, 2, 3, 4]), -8)

    def test_safe_diff_all_None(self):
        self.assertEqual(functions.safeDiff([None, None, None, None]), None)

    def test_safe_diff_mixed(self):
        self.assertEqual(functions.safeDiff([10, None, 5, None]), 5)

    # Test safeLen()
    def test_safe_len_None(self):
        with self.assertRaises(TypeError):
            functions.safeLen(None)

    def test_safe_len_empty_list(self):
        self.assertEqual(functions.safeLen([]), 0)

    def test_safe_len_all_numbers(self):
        self.assertEqual(functions.safeLen([1, 2, 3, 4]), 4)

    def test_safe_len_all_None(self):
        self.assertEqual(functions.safeLen([None, None, None, None]), 0)

    def test_safe_len_mixed(self):
        self.assertEqual(functions.safeLen([10, None, 5, None]), 2)

    # Test safeDiv()
    def test_safe_div_None_None(self):
        self.assertEqual(functions.safeDiv(None, None), None)

    def test_safe_div_5_None(self):
        self.assertEqual(functions.safeDiv(5, None), None)

    def test_safe_div_5_0(self):
        self.assertEqual(functions.safeDiv(5, 0), None)

    def test_safe_div_0_10(self):
        self.assertEqual(functions.safeDiv(0, 10), 0)

    def test_safe_div_10_5(self):
        self.assertEqual(functions.safeDiv(10, 5), 2)

    # Test safePow()
    def test_save_pow_None_None(self):
        self.assertEqual(functions.safePow(None, None), None)

    def test_save_pow_5_None(self):
        self.assertEqual(functions.safePow(5, None), None)

    def test_save_pow_5_0(self):
        self.assertEqual(functions.safePow(5, 0), 1.0)

    def test_save_pow_0_10(self):
        self.assertEqual(functions.safePow(0, 10), 0)

    def test_save_pow_10_5(self):
        self.assertEqual(functions.safePow(10, 5), 100000.0)

    # Test safeMul()
    def test_safe_mul_None_None(self):
        self.assertEqual(functions.safeMul(None, None), None)

    def test_safe_mul_5_None(self):
        self.assertEqual(functions.safeMul(5, None), None)

    def test_safe_mul_5_0(self):
        self.assertEqual(functions.safeMul(5, 0), 0.0)

    def test_safe_mul_0_10(self):
        self.assertEqual(functions.safeMul(0, 10), 0)

    def test_safe_mul_10_5(self):
        self.assertEqual(functions.safeMul(10, 5), 50.0)

    # Test safeSubtract()
    def test_safe_subtract_None_None(self):
        self.assertEqual(functions.safeSubtract(None, None), None)

    def test_safe_subtract_5_None(self):
        self.assertEqual(functions.safeSubtract(5, None), None)

    def test_safe_subtract_5_0(self):
        self.assertEqual(functions.safeSubtract(5, 0), 5.0)

    def test_safe_subtract_0_10(self):
        self.assertEqual(functions.safeSubtract(0, 10), -10)

    def test_safe_subtract_10_5(self):
        self.assertEqual(functions.safeSubtract(10, 5), 5)

    # Test safeAvg()
    def test_safe_avg_None(self):
        with self.assertRaises(TypeError):
            functions.safeAvg(None)

    def test_safe_avg_empty_list(self):
        self.assertEqual(functions.safeAvg([]), None)

    def test_safe_avg_all_numbers(self):
        self.assertEqual(functions.safeAvg([1, 2, 3, 4]), 2.5)

    def test_safe_avg_all_None(self):
        self.assertEqual(functions.safeAvg([None, None, None, None]), None)

    def test_safe_avg_mixed(self):
        self.assertEqual(functions.safeAvg([10, None, 5, None]), 7.5)

    # Test safeStdDev()
    def test_safe_stddev_None(self):
        with self.assertRaises(TypeError):
            functions.safeStdDev(None)

    def test_safe_stddev_empty_list(self):
        self.assertEqual(functions.safeStdDev([]), None)

    def test_safe_stddev_all_numbers(self):
        self.assertEqual(functions.safeStdDev([1, 2, 3, 4]), 1.118033988749895)

    def test_safe_stddev_all_None(self):
        self.assertEqual(functions.safeStdDev([None, None, None, None]), None)

    def test_safe_stddev_mixed(self):
        self.assertEqual(functions.safeStdDev([10, None, 5, None]), 2.5)

    # Test safeLast()
    def test_safe_last_None(self):
        with self.assertRaises(TypeError):
            functions.safeLast(None)

    def test_safe_last_empty_list(self):
        self.assertEqual(functions.safeLast([]), None)

    def test_safe_last_all_numbers(self):
        self.assertEqual(functions.safeLast([1, 2, 3, 4]), 4)

    def test_safe_last_all_None(self):
        self.assertEqual(functions.safeLast([None, None, None, None]), None)

    def test_safe_last_mixed(self):
        self.assertEqual(functions.safeLast([10, None, 5, None]), 5)

    # Test safeMin()
    def test_safe_min_None(self):
        with self.assertRaises(TypeError):
            functions.safeMin(None)

    def test_safe_min_empty_list(self):
        self.assertEqual(functions.safeMin([]), None)

    def test_safe_min_all_numbers(self):
        self.assertEqual(functions.safeMin([1, 2, 3, 4]), 1)

    def test_safe_min_all_None(self):
        self.assertEqual(functions.safeMin([None, None, None, None]), None)

    def test_safe_min_mixed(self):
        self.assertEqual(functions.safeMin([10, None, 5, None]), 5)

    # Test safeMax()
    def test_safe_max_None(self):
        with self.assertRaises(TypeError):
            functions.safeMax(None)

    def test_safe_max_empty_list(self):
        self.assertEqual(functions.safeMax([]), None)

    def test_safe_max_all_numbers(self):
        self.assertEqual(functions.safeMax([1, 2, 3, 4]), 4)

    def test_safe_max_all_None(self):
        self.assertEqual(functions.safeMax([None, None, None, None]), None)

    def test_safe_max_mixed(self):
        self.assertEqual(functions.safeMax([10, None, 5, None]), 10)

    # Test safeAbs()
    def test_safe_abs_None(self):
        self.assertEqual(functions.safeAbs(None), None)

    def test_safe_abs_empty_list(self):
        with self.assertRaises(TypeError):
            functions.safeAbs([])

    def test_safe_abs_pos_number(self):
        self.assertEqual(functions.safeAbs(1), 1)

    def test_safe_abs_neg_numbers(self):
        self.assertEqual(functions.safeAbs(-1), 1)

    def test_safe_abs_zero(self):
        self.assertEqual(functions.safeAbs(0), 0)

    # Test safeMap()
    def test_safe_map_None(self):
        with self.assertRaises(TypeError):
            functions.safeMap(abs, None)

    def test_safe_map_empty_list(self):
        self.assertEqual(functions.safeMap(abs, []), None)

    def test_safe_map_all_numbers(self):
        self.assertEqual(functions.safeMap(abs, [1, 2, 3, 4]), [1, 2, 3, 4])

    def test_safe_map_all_None(self):
        self.assertEqual(functions.safeMap(abs, [None, None, None, None]),
                         None)

    def test_safe_map_mixed(self):
        self.assertEqual(functions.safeMap(abs, [10, None, 5, None]), [10, 5])

    # Test gcd()
    def test_gcd_None_None(self):
        with self.assertRaises(TypeError):
            functions.gcd(None, None)

    def test_gcd_5_None(self):
        with self.assertRaises(TypeError):
            functions.gcd(5, None)

    def test_gcd_5_0(self):
        self.assertEqual(functions.gcd(5, 0), 5)

    def test_gcd_0_10(self):
        self.assertEqual(functions.gcd(0, 10), 10)

    def test_gcd_10_5(self):
        self.assertEqual(functions.gcd(10, 5), 5)

    # Test lcm()
    def test_lcm_None_None(self):
        self.assertEqual(functions.lcm(None, None), None)

    def test_lcm_5_None(self):
        with self.assertRaises(TypeError):
            functions.lcm(5, None)

    def test_lcm_5_0(self):
        self.assertEqual(functions.lcm(5, 0), 0)

    def test_lcm_0_10(self):
        self.assertEqual(functions.lcm(0, 10), 0)

    def test_lcm_10_5(self):
        self.assertEqual(functions.lcm(10, 5), 10)

    # Test normalize()
    def test_normalize_empty(self):
        self.assertEqual(functions.normalize([]), [])

    def test_normalize_None_values(self):
        seriesList = []
        seriesList.append(TimeSeries("collectd.test-db{0}.load.value", 0, 5, 1,
                                     [None, None, None, None, None]))
        self.assertEqual(functions.normalize([seriesList]),
                         (seriesList, 0, 5, 1))

    def test_normalize_generate_series_list_input(self):
        seriesList = self._generate_series_list(config=[range(101),
                                                        range(101)])
        self.assertEqual(functions.normalize([seriesList]),
                         (seriesList, seriesList[0].start,
                          seriesList[0].end, 1))

    # Test matchSeries()
    def test_match_series_assert(self):
        seriesList = self._generate_series_list()
        with self.assertRaises(AssertionError) as context:
            functions.matchSeries(seriesList[0], [])
        self.assertIn('The number of series in each argument '
                      'must be the same', str(context.exception))

    def test_match_series_empty(self):
        results = functions.matchSeries([], [])
        for i, (series1, series2) in enumerate(results):
            self.assertEqual(series1, [])
            self.assertEqual(series2, [])

    def test_match_series(self):
        seriesList1 = [
            TimeSeries('collectd.test-db3.load.value', 0, 1, 1, [3, 30, 31]),
            TimeSeries('collectd.test-db1.load.value', 0, 1, 1, [1, 10, 11]),
            TimeSeries('collectd.test-db2.load.value', 0, 1, 1, [2, 20, 21]),
            TimeSeries('collectd.test-db4.load.value', 0, 1, 1, [4, 40, 41]),
        ]
        seriesList2 = [
            TimeSeries('collectd.test-db4.load.value', 0, 1, 1, [4, 8, 12]),
            TimeSeries('collectd.test-db3.load.value', 0, 1, 1, [3, 7, 11]),
            TimeSeries('collectd.test-db1.load.value', 0, 1, 1, [1, 5, 9]),
            TimeSeries('collectd.test-db2.load.value', 0, 1, 1, [2, 6, 10]),
        ]
        expectedResult = [[
            TimeSeries('collectd.test-db1.load.value', 0, 1, 1, [1, 10, 11]),
            TimeSeries('collectd.test-db2.load.value', 0, 1, 1, [2, 20, 21]),
            TimeSeries('collectd.test-db3.load.value', 0, 1, 1, [3, 30, 31]),
            TimeSeries('collectd.test-db4.load.value', 0, 1, 1, [4, 40, 41]),
        ], [
            TimeSeries('collectd.test-db1.load.value', 0, 1, 1, [1, 5, 9]),
            TimeSeries('collectd.test-db2.load.value', 0, 1, 1, [2, 6, 10]),
            TimeSeries('collectd.test-db3.load.value', 0, 1, 1, [3, 7, 11]),
            TimeSeries('collectd.test-db4.load.value', 0, 1, 1, [4, 8, 12]),
        ]]
        results = functions.matchSeries(copy.deepcopy(seriesList1),
                                        copy.deepcopy(seriesList2))
        for i, (series1, series2) in enumerate(results):
            self.assertEqual(series1, expectedResult[0][i])
            self.assertEqual(series2, expectedResult[1][i])

    # Test formatPathExpressions()
    def test_format_path_expressions_empty_list(self):
        self.assertEqual(functions.formatPathExpressions([]), '')

    def test_format_path_expressions(self):
        seriesList = self._generate_series_list()
        self.assertEqual(functions.formatPathExpressions(seriesList),
                         "collectd.test-db1.load.value,"
                         "collectd.test-db2.load.value,"
                         "collectd.test-db3.load.value,"
                         "collectd.test-db4.load.value")

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

        def n_percentile(perc, expect):
            seriesList = []
            expected = []
            for i, c in enumerate(config):
                seriesList.append(TimeSeries('Test(%d)' % i, 0, len(c), 1, c))
                expected.append(TimeSeries('nPercentile(Test(%d), %d)' %
                                           (i, perc), 0, len(c), 1,
                                           expect[i] * len(c)))
            result = functions.nPercentile({}, seriesList, perc)
            self.assertEqual(expected, result)

        n_percentile(30, [[20], [31], [61], [91], [30], [60], [90], [90]])
        n_percentile(90, [[50], [91], [181], [271], [90], [180], [270], [270]])
        n_percentile(95, [[50], [96], [191], [286], [95], [190], [285], [285]])

    def _generate_series_list(self, config=(
        range(101),
        range(2, 103),
        [1] * 2 + [None] * 90 + [1] * 2 + [None] * 7,
        []
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
        seriesList.pop()
        percent = 50
        results = functions.removeAbovePercentile({}, seriesList, percent)
        for result, exc in zip(results, [[], [51, 52]]):
            self.assertListEqual(return_greater(result, percent), exc)

    def test_remove_below_percentile(self):
        seriesList = self._generate_series_list()
        seriesList.pop()
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
            if None not in series:
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

    def test_transform_null_reference(self):
        seriesList = self._generate_series_list()
        transform = -5
        referenceSeries = copy.deepcopy(seriesList[0])
        for k, v in enumerate(referenceSeries):
            if k % 2 != 0:
                referenceSeries[k] = None

        results = functions.transformNull({}, copy.deepcopy(seriesList),
                                          transform, [referenceSeries])

        for counter, series in enumerate(seriesList):
            if None not in series:
                continue
            # Anywhere a None was in the original series, verify it
            # was transformed to the given value if a value existed
            # in the reference series
            for i, value in enumerate(series):
                if value is None and referenceSeries[i] is not None:
                    result_val = results[counter][i]
                    self.assertEqual(
                        transform, result_val,
                        "Transformed value should be {0}, not {1}".format(
                            transform, result_val))

    def test_transform_null_reference_empty(self):
        seriesList = self._generate_series_list()
        transform = -5
        referenceSeries = []

        results = functions.transformNull({}, copy.deepcopy(seriesList),
                                          transform, [referenceSeries])

        for counter, series in enumerate(seriesList):
            if None not in series:
                continue
            # If the None values weren't transformed, there is a problem
            self.assertNotIn(None, results[counter],
                             "tranformNull should remove all None values")
            # Anywhere a None was in the original series, verify it
            # was transformed to the given value if a value existed
            for i, value in enumerate(series):
                if value is None:
                    result_val = results[counter][i]
                    self.assertEqual(
                        transform, result_val,
                        "Transformed value should be {0}, not {1}".format(
                            transform, result_val))

    def test_group(self):
        seriesList = [
            TimeSeries('collectd.test-db1.load.value',
                       0, 600, 60, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]),
            TimeSeries('collectd.test-db2.load.value',
                       0, 600, 60, [None] * 10),
            TimeSeries('collectd.test-db3.load.value',
                       0, 600, 60, [1, 2, None, None, None, 6, 7, 8, 9, 10]),
            TimeSeries('collectd.test-db4.load.value',
                       0, 600, 60, [1, 2, 3, 4, 5, 6, 7, 8, 9, None]),
        ]
        for series in seriesList:
            series.pathExpression = series.name

        request_context = {}
        result = functions.group(request_context, seriesList[0],
                                 seriesList[1], seriesList[2], seriesList[3])
        self.assertEqual(result, [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, None, None,
                                  None, None, None, None, None, None, None,
                                  None, 1, 2, None, None, None, 6, 7, 8, 9,
                                  10, 1, 2, 3, 4, 5, 6, 7, 8, 9, None])

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

    def test_average_series_wildcards_empty_series_int_position(self):
        self.assertEqual(functions.averageSeriesWithWildcards({}, [], 0), [])

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
            TimeSeries('group.server2.reduce.mock', 0, 1, 1, [None]),
            TimeSeries('group.server2.reduce.mock', 0, 1, 1, [None])
        ]
        resultSeriesList = [TimeSeries('mock(series)', 0, 1, 1, [None])]
        mock = MagicMock(return_value=resultSeriesList)
        with patch.dict(app.config['GRAPHITE']['functions'], {'mock': mock}):
            results = functions.reduceSeries({}, copy.deepcopy(inputList),
                                             "mock", 2, "metric1", "metric2")
            self.assertEqual(results, expectedResult)
        self.assertEqual(mock.mock_calls, [
            call({}, *[[x] for x in inputList[0]]),
            call({}, *[[x] for x in inputList[1]]),
        ])

    def test_reduceSeries_asPercent(self):
        seriesList = [
            TimeSeries('group.server1.bytes_used', 0, 1, 1, [1]),
            TimeSeries('group.server1.total_bytes', 0, 1, 1, [2]),
            TimeSeries('group.server2.bytes_used', 0, 1, 1, [3]),
            TimeSeries('group.server2.total_bytes', 0, 1, 1, [4]),
        ]
        for series in seriesList:
            series.pathExpression = "tempPath"
        expectedResult = [
            # 50 == 100 * 1 / 2
            TimeSeries('group.server1.reduce.asPercent', 0, 1, 1, [50]),
            # 100 * 3 / 4
            TimeSeries('group.server2.reduce.asPercent', 0, 1, 1, [75]),
        ]
        mappedResult = (
            [seriesList[0]], [seriesList[1]], [seriesList[2]], [seriesList[3]])
        results = functions.reduceSeries(
            {}, copy.deepcopy(mappedResult),
            "asPercent", 2, "bytes_used", "total_bytes")
        self.assertEqual(results, expectedResult)

    def test_pow(self):
        seriesList = self._generate_series_list()
        factor = 2
        # Leave the original seriesList undisturbed for verification
        results = functions.pow({}, copy.deepcopy(seriesList), factor)
        for i, series in enumerate(results):
            for counter, value in enumerate(series):
                if value is None:
                    continue
                original_value = seriesList[i][counter]
                expected_value = math.pow(original_value, factor)
                self.assertEqual(value, expected_value)

    def test_sum_series_empty(self):
        self.assertEqual(functions.sumSeries({}, []), [])

    def test_sum_series(self):
        series = self._generate_series_list()
        [sum_] = functions.sumSeries({}, series)
        self.assertEqual(sum_.pathExpression,
                         "sumSeries(collectd.test-db1.load.value,"
                         "collectd.test-db2.load.value,"
                         "collectd.test-db3.load.value,"
                         "collectd.test-db4.load.value)")
        self.assertEqual(sum_[:3], [3, 5, 6])

    def test_sum_series_wildcards_empty_series_int_position(self):
        self.assertEqual(functions.sumSeriesWithWildcards({}, [], 0), [])

    def test_sum_series_wildcards(self):
        series = self._generate_series_list()
        [sum_] = functions.sumSeriesWithWildcards({}, series, 1)
        self.assertEqual(sum_.pathExpression,
                         "sumSeries(collectd.test-db4.load.value,"
                         "sumSeries(collectd.test-db3.load.value,"
                         "sumSeries(collectd.test-db1.load.value,"
                         "collectd.test-db2.load.value)))")
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

    def test_changed(self):
        series = self._generate_series_list(config=[[0, 1, 2, 2, 2, 3, 3, 2]])
        [changed] = functions.changed({}, series)
        self.assertEqual(list(changed), [0, 1, 1, 0, 0, 1, 0, 1])

    def test_as_percent(self):
        series = self._generate_series_list()
        perc = functions.asPercent({}, series)[0]
        self.assertEqual(perc[:2], [0.0, 20.0])
        self.assertEqual(perc[3], 37.5)

        with self.assertRaises(ValueError):
            functions.asPercent({}, series[:2], [1, 2, 3])

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

    def test_multiply_series_wildcards(self):
        series = self._generate_series_list()
        mul = functions.multiplySeriesWithWildcards({}, series[:2], 1)[0]
        self.assertEqual(mul[:3], [0, 3, 8])

        mul = functions.multiplySeriesWithWildcards({}, series[:1], 1)[0]
        self.assertEqual(mul[:3], [0, 1, 2])

    def test_weighted_average(self):
        series = self._generate_series_list()
        weight = functions.weightedAverage({}, [series[0]], [series[1]], 0)
        self.assertEqual(weight[:3], [0, 1, 2])

    def test_moving_median_empty_series(self):
        self.assertEqual(functions.movingMedian({}, [], ""), [])

    def test_moving_median_returns_none(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+10, start+15, 1, range(start, start+15)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value', 10, 25, 1,
                           [None] * 15)
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        expectedResults = [
            TimeSeries('movingMedian(collectd.test-db0.load.value,10)',
                       20, 25, 1, [None, None, None, None, None])
        ]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingMedian({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 10)

        self.assertEqual(result, expectedResults)

    def test_moving_median_returns_half_none(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+10, start+20, 1, range(0, 10)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value', 10, 30, 1,
                           [None] * 10 + list(range(0, 10)))
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        expectedResults = [
            TimeSeries('movingMedian(collectd.test-db0.load.value,10)',
                       20, 30, 1, [None, 0, 1, 1, 2, 2, 3, 3, 4, 4])
        ]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingMedian({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 10)

        self.assertEqual(result, expectedResults)

    def test_moving_median_returns_empty(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+600, start+700, 1, range(start, start+100)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            return []

        expectedResults = []

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingMedian({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 60)

        self.assertEqual(result, expectedResults)

    def test_moving_median(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+600, start+700, 1, range(start, start+100)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            return gen_series_list()

        expectedResults = [[
            TimeSeries('movingMedian(collectd.test-db0.load.value,60)',
                       660, 700, 1, range(30, 70)),
        ], [
            TimeSeries('movingMedian(collectd.test-db0.load.value,"-1min")',
                       660, 700, 1, range(30, 70)),
        ]]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingMedian({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 60)
            self.assertEqual(result, expectedResults[0])

            result = functions.movingMedian({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, "-1min")
            self.assertEqual(result, expectedResults[1])

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

    def test_moving_average_empty_series(self):
        self.assertEqual(functions.movingAverage({}, [], ""), [])

    def test_moving_average_returns_none(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+10, start+15, 1, range(start, start+15)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value', 10, 25, 1,
                           [None] * 15)
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        expectedResults = [
            TimeSeries('movingAverage(collectd.test-db0.load.value,10)',
                       20, 25, 1, [None, None, None, None, None])
        ]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingAverage({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 10)

        self.assertEqual(result, expectedResults)

    def test_moving_average_returns_half_none(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+10, start+20, 1, range(0, 10)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value', 10, 30, 1,
                           [None] * 10 + list(range(0, 10)))
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        expectedResults = [
            TimeSeries('movingAverage(collectd.test-db0.load.value,10)',
                       20, 30, 1, [None, 0.0, 0.5, 1.0, 1.5,
                                   2.0, 2.5, 3.0, 3.5, 4.0])
        ]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingAverage({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 10)

        self.assertEqual(result, expectedResults)

    def test_moving_average_returns_empty(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+600, start+700, 1, range(start, start+100)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            return []

        expectedResults = []

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingAverage({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 60)

        self.assertEqual(result, expectedResults)

    def test_moving_average(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+600, start+700, 1, range(start, start+100)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            return gen_series_list()

        def frange(x, y, jump):
            while x < y:
                yield x
                x += jump

        expectedResults = [[
            TimeSeries('movingAverage(collectd.test-db0.load.value,60)',
                       660, 700, 1, frange(29.5, 69.5, 1)),
        ], [
            TimeSeries('movingAverage(collectd.test-db0.load.value,"-1min")',
                       660, 700, 1, frange(29.5, 69.5, 1)),
        ]]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.movingAverage({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, 60)
            self.assertEqual(result, expectedResults[0])

            result = functions.movingAverage({
                'args': ({}, {}),
                'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series, "-1min")
            self.assertEqual(result, expectedResults[1])

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

    def test_integral_by_interval(self):
        series = self._generate_series_list(
            config=[list(range(1, 10)) * 9 + [None] * 10])
        integral = functions.integralByInterval({
            'startTime': parseATTime('-101s')
        }, series, '100s')[0]
        self.assertEqual(integral[:3], [1, 3, 6])
        self.assertEqual(integral[-11:], [405] * 11)

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

    def test_area_between(self):
        series = self._generate_series_list()
        lower, upper = functions.areaBetween({}, series[0], series[1])
        self.assertEqual(lower.options, {'stacked': True, 'invisible': True})
        self.assertEqual(upper.options, {'stacked': True})

    def test_cactistyle(self):
        series = self._generate_series_list()
        cacti = functions.cactiStyle({}, series)
        self.assertEqual(
            cacti[0].name,
            "collectd.test-db1.load.value Current:100.00    Max:100.00    "
            "Min:0.00    ")

        series = self._generate_series_list()
        cacti = functions.cactiStyle({}, series, 'si')
        self.assertEqual(
            cacti[0].name,
            "collectd.test-db1.load.value Current:100.00    Max:100.00    "
            "Min:0.00    ")

        series = self._generate_series_list(config=[[None] * 100])
        cacti = functions.cactiStyle({}, series)
        self.assertEqual(
            cacti[0].name,
            "collectd.test-db1.load.value Current:nan     Max:nan     "
            "Min:nan     ")

        cacti = functions.cactiStyle({}, [])
        self.assertEqual(cacti, [])

    def test_alias_by_metric(self):
        series = self._generate_series_list(config=[range(100)])
        series[0].name = 'scaleToSeconds(%s,10)' % series[0].name
        alias = functions.aliasByMetric({}, series)[0]
        self.assertEqual(alias.name, "value")

    def test_legend_value(self):
        series = self._generate_series_list(config=[range(100)])
        legend = functions.legendValue({}, series, 'min', 'max', 'avg')[0]
        self.assertEqual(
            legend.name,
            "collectd.test-db1.load.value (min: 0) (max: 99) (avg: 49.5)")

        series = self._generate_series_list(config=[range(100)])
        series[0].name = 'load.value'
        legend = functions.legendValue({}, series, 'avg', 'si')[0]
        self.assertEqual(
            legend.name,
            "load.value          avg  49.50     ")

        series = self._generate_series_list(config=[range(100)])
        legend = functions.legendValue({}, series, 'lol')[0]
        self.assertEqual(
            legend.name, "collectd.test-db1.load.value (lol: (?))")

        series = self._generate_series_list(config=[[None] * 100])
        legend = functions.legendValue({}, series, 'min')[0]
        self.assertEqual(
            legend.name, "collectd.test-db1.load.value (min: None)")

    def test_substr(self):
        series = self._generate_series_list(config=[range(100)])
        sub = functions.substr({}, series, 1)[0]
        self.assertEqual(sub.name, "test-db1.load.value")

        series = functions.alias(
            {}, self._generate_series_list(config=[range(100)]),
            '(foo.bar, "baz")')
        sub = functions.substr({}, series, 1)[0]
        self.assertEqual(sub.name, "bar")

        series = self._generate_series_list(config=[range(100)])
        sub = functions.substr({}, series, 0, 2)[0]
        self.assertEqual(sub.name, "collectd.test-db1")

    def test_log(self):
        series = self._generate_series_list(config=[range(101)])
        log = functions.logarithm({}, series)[0]
        self.assertEqual(log[0], None)
        self.assertEqual(log[1], 0)
        self.assertEqual(log[10], 1)
        self.assertEqual(log[100], 2)

        series = self._generate_series_list(config=[[None] * 100])
        log = functions.logarithm({}, series)[0]
        self.assertEqual(list(log), [None] * 100)

    def test_max_above(self):
        series = self._generate_series_list(config=[range(100)])
        max_above = functions.maximumAbove({}, series, 200)
        self.assertEqual(max_above, [])
        max_above = functions.maximumAbove({}, series, 98)
        self.assertEqual(max_above, series)

    def test_min_above(self):
        series = self._generate_series_list(config=[range(100, 200)])
        min_above = functions.minimumAbove({}, series, 200)
        self.assertEqual(min_above, [])
        min_above = functions.minimumAbove({}, series, 99)
        self.assertEqual(min_above, series)

    def test_max_below(self):
        series = self._generate_series_list(config=[range(100)])
        max_below = functions.maximumBelow({}, series, 98)
        self.assertEqual(max_below, [])
        max_below = functions.maximumBelow({}, series, 100)
        self.assertEqual(max_below, series)

    def test_min_below(self):
        series = self._generate_series_list(config=[range(100)])
        min_below = functions.minimumBelow({}, series, -1)
        self.assertEqual(min_below, [])
        min_below = functions.minimumBelow({}, series, 0)
        self.assertEqual(min_below, series)

    def test_highest_current(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(10, 110),
                                                    range(200, 300)])
        highest = functions.highestCurrent({}, series)[0]
        self.assertEqual(highest.name, "collectd.test-db3.load.value")

        highest = functions.highestCurrent({}, series, 2)
        self.assertEqual(highest[0].name, "collectd.test-db2.load.value")

    def test_lowest_current(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(10, 110),
                                                    range(200, 300)])
        lowest = functions.lowestCurrent({}, series)[0]
        self.assertEqual(lowest.name, "collectd.test-db1.load.value")

    def test_current_above(self):
        series = self._generate_series_list(config=[range(100)])
        above = functions.currentAbove({}, series, 200)
        self.assertEqual(len(above), 0)

        above = functions.currentAbove({}, series, 98)
        self.assertEqual(above, series)

    def test_current_below(self):
        series = self._generate_series_list(config=[range(100)])
        below = functions.currentBelow({}, series, 50)
        self.assertEqual(len(below), 0)
        below = functions.currentBelow({}, series, 100)
        self.assertEqual(below, series)

    def test_highest_average(self):
        series = self._generate_series_list(config=[
            range(100),
            range(50, 150),
            list(range(150, 200)) + [None] * 50])
        highest = functions.highestAverage({}, series, 2)
        self.assertEqual(len(highest), 2)
        self.assertEqual(highest, [series[1], series[2]])

        highest = functions.highestAverage({}, series)
        self.assertEqual(highest, [series[2]])

    def test_lowest_average(self):
        series = self._generate_series_list(config=[
            range(100),
            range(50, 150),
            list(range(150, 200)) + [None] * 50])
        lowest = functions.lowestAverage({}, series, 2)
        self.assertEqual(len(lowest), 2)
        self.assertEqual(lowest, [series[0], series[1]])

        lowest = functions.lowestAverage({}, series)
        self.assertEqual(lowest, [series[0]])

    def test_average_above(self):
        series = self._generate_series_list(config=[range(100)])
        above = functions.averageAbove({}, series, 50)
        self.assertEqual(len(above), 0)

        above = functions.averageAbove({}, series, 40)
        self.assertEqual(above, series)

    def test_average_below(self):
        series = self._generate_series_list(config=[range(100)])
        below = functions.averageBelow({}, series, 40)
        self.assertEqual(len(below), 0)

        below = functions.averageBelow({}, series, 50)
        self.assertEqual(below, series)

    def test_average_outside_percentile(self):
        series = self._generate_series_list(
            config=[range(i, i+100) for i in range(50)])
        outside = functions.averageOutsidePercentile({}, series, 95)
        self.assertEqual(outside, series[:3] + series[-2:])

        outside = functions.averageOutsidePercentile({}, series, 5)
        self.assertEqual(outside, series[:3] + series[-2:])

    def test_remove_between_percentile(self):
        series = self._generate_series_list(
            config=[range(i, i+100) for i in range(50)])
        not_between = functions.removeBetweenPercentile({}, series, 95)
        self.assertEqual(not_between, series[:3] + series[-2:])

        not_between = functions.removeBetweenPercentile({}, series, 5)
        self.assertEqual(not_between, series[:3] + series[-2:])

    def test_sort_by_name(self):
        series = list(reversed(self._generate_series_list(
            config=[range(100) for i in range(10)])))
        sorted_s = functions.sortByName({}, series)
        self.assertEqual(sorted_s[0].name, series[-1].name)

        sorted_n = functions.sortByName({}, series, True)
        self.assertEqual(sorted_n[0].name, series[-1].name)

    def test_sort_by_total(self):
        series = self._generate_series_list(
            config=[range(i, i+100) for i in range(10)])
        sorted_s = functions.sortByTotal({}, series)
        self.assertEqual(sorted_s[0].name, series[-1].name)

    def test_sort_by_maxima(self):
        series = list(reversed(self._generate_series_list(
            config=[range(i, i+100) for i in range(10)])))
        sorted_s = functions.sortByMaxima({}, series)
        self.assertEqual(sorted_s[0].name, series[-1].name)

    def test_sort_by_minima(self):
        series = list(reversed(self._generate_series_list(
            config=[range(i, i+100) for i in range(10)])))
        sorted_s = functions.sortByMinima({}, series)
        self.assertEqual(sorted_s[0].name, series[-1].name)

    def test_use_series_above(self):
        series = self._generate_series_list(
            config=[list(range(90)) + [None] * 10])
        series[0].pathExpression = 'bar'

        for s in series:
            self.write_series(s)

        series[0].name = 'foo'

        ctx = {
            'startTime': parseATTime('-100s'),
            'endTime': parseATTime('now'),
        }
        above = functions.useSeriesAbove(ctx, series, 10, 'foo', 'bar')[0]
        self.assertEqual(above[0], 2)

        above = functions.useSeriesAbove(ctx, series, 100, 'foo', 'bar')
        self.assertEqual(len(above), 0)

        above = functions.useSeriesAbove(ctx, series, 10, 'foo', 'baz')
        self.assertEqual(len(above), 0)

    def test_most_deviant(self):
        series = self._generate_series_list(config=[
            range(1, i * 100, i) for i in range(1, 10)] + [[None] * 100])
        deviant = functions.mostDeviant({}, series, 8)
        self.assertEqual(deviant[0].name, 'collectd.test-db9.load.value')

    def test_stdev(self):
        series = self._generate_series_list(config=[
            [x**1.5 for x in range(100)], [None] * 100])
        dev = functions.stdev({}, series, 10)[0]
        self.assertEqual(dev[1], 0.5)

    def test_stdev_math_domain(self):
        # This data set is enough to trigger a math domain error in stdev.
        # The last two data points should be NaN.
        inputData = [0.9, 0.1, 0.5, 0.7, 0.5, 0.4, 0.4, 0.3, 0.6,
                     0.6333333333333333, 1.3,
                     0.6333333333333333, 0.6185185185185186,
                     0.3, 0.5, 0.6, 0.3, 1.0, 0.6, 0.9, 0.4,
                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
        series = [
            TimeSeries('collectd.test-db0.load.value', 600, 760, 5, inputData)
        ]
        series[0].pathExpression = series[0].name

        result = functions.stdev({}, series, 10)[0]
        self.assertEqual(result[-2:], [None, None])

    def test_holt_winters_analysis_none(self):
        seriesList = TimeSeries('collectd.test-db0.load.value',
                                660, 700, 1, [None])
        expectedResults = {
            'predictions': TimeSeries(
                'holtWintersForecast(collectd.test-db0.load.value)',
                660, 700, 1, [None]),
            'deviations': TimeSeries(
                'holtWintersDeviation(collectd.test-db0.load.value)',
                660, 700, 1, [0]),
            'seasonals': [0],
            'slopes': [0],
            'intercepts': [None]
        }

        result = functions.holtWintersAnalysis(seriesList)
        self.assertEqual(result, expectedResults)

    def test_holt_winters_forecast(self):
        def gen_series_list(start=0):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start+600, start+700, 1, range(start, start+100)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(10)

        def mock_evaluate(reqCtx, tokens, store=None):
            return gen_series_list()

        expectedResults = [
            TimeSeries('holtWintersForecast(collectd.test-db0.load.value)',
                       605400, 700, 1, [])
        ]

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.holtWintersForecast({
                'args': ({}, {}),
                'startTime': datetime(1970, 2, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 2, 1, 0, 9, 0, 0, pytz.utc),
                'data': [],
            }, series)
        self.assertEqual(result, expectedResults)

    def test_holt_winters(self):
        points = 10
        step = 600
        start_time = 2678400  # 1970-02-01
        week_seconds = 7 * 86400

        def hw_range(x, y, jump):
            while x < y:
                yield (x / jump) % 10
                x += jump

        def gen_series_list(start=0, points=10):
            seriesList = [
                TimeSeries('collectd.test-db0.load.value',
                           start, start+(points*step), step,
                           hw_range(0, points*step, step)),
            ]
            for series in seriesList:
                series.pathExpression = series.name
            return seriesList

        series = gen_series_list(start_time, points)

        def mock_evaluate(reqCtx, tokens, store=None):
            return gen_series_list(start_time - week_seconds,
                                   (week_seconds / step) + points)

        expectedResults = [[
            TimeSeries(
                'holtWintersConfidenceLower(collectd.test-db0.load.value)',
                start_time, start_time+(points*step), step,
                [0.2841206166091448, 1.0581027098774411, 0.3338172102994683,
                 0.5116859493263242, -0.18199175514936972, 0.2366173792019426,
                 -1.2941554508809152, -0.513426806531049, -0.7970905542723132,
                 0.09868900726536012]
            ),
            TimeSeries(
                'holtWintersConfidenceUpper(collectd.test-db0.load.value)',
                start_time, start_time+(points*step), step,
                [8.424944558327624, 9.409422251880809, 10.607070189221787,
                 10.288439865038768, 9.491556863132963, 9.474595784593738,
                 8.572310478053845, 8.897670449095346, 8.941566968508148,
                 9.409728797779282]
            ),
        ], [
            TimeSeries(
                'holtWintersConfidenceArea(collectd.test-db0.load.value)',
                start_time, start_time+(points*step), step,
                [0.2841206166091448, 1.0581027098774411, 0.3338172102994683,
                 0.5116859493263242, -0.18199175514936972, 0.2366173792019426,
                 -1.2941554508809152, -0.513426806531049, -0.7970905542723132,
                 0.09868900726536012]
            ),
            TimeSeries(
                'holtWintersConfidenceArea(collectd.test-db0.load.value)',
                start_time, start_time+(points*step), step,
                [8.424944558327624, 9.409422251880809, 10.607070189221787,
                 10.288439865038768, 9.491556863132963, 9.474595784593738,
                 8.572310478053845, 8.897670449095346, 8.941566968508148,
                 9.409728797779282]
            ),
        ], [
            TimeSeries(
                'holtWintersAberration(collectd.test-db0.load.value)',
                start_time, start_time+(points*step), step,
                [-0.2841206166091448, -0.05810270987744115,
                 0, 0, 0, 0, 0, 0, 0, 0]
            )
        ]]
        expectedResults[1][0].options = {'invisible': True, 'stacked': True}
        expectedResults[1][1].options = {'stacked': True}

        with patch('graphite_api.functions.evaluateTokens', mock_evaluate):
            result = functions.holtWintersConfidenceBands({
                'args': ({}, {}),
                'startTime': datetime(1970, 2, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 2, 1, 0, 9, 0, 0, pytz.utc),
                'data': []
                }, series)
            self.assertEqual(result, expectedResults[0])

            result = functions.holtWintersConfidenceArea({
                'args': ({}, {}),
                'startTime': datetime(1970, 2, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 2, 1, 0, 9, 0, 0, pytz.utc),
                'data': []
                }, series)
            self.assertEqual(result, expectedResults[1])

            result = functions.holtWintersAberration({
                'args': ({}, {}),
                'startTime': datetime(1970, 2, 1, 0, 0, 0, 0, pytz.utc),
                'endTime': datetime(1970, 2, 1, 0, 9, 0, 0, pytz.utc),
                'data': []
                }, series)
            self.assertEqual(result, expectedResults[2])

    def test_dashed(self):
        series = self._generate_series_list(config=[range(100)])
        dashed = functions.dashed({}, series)[0]
        self.assertEqual(dashed.options, {'dashed': 5})

        dashed = functions.dashed({}, series, 12)[0]
        self.assertEqual(dashed.options, {'dashed': 12})

    def test_time_stack(self):
        timespan = 3600 * 24 * 8  # 8 days
        stop = int(time.time())
        step = 100
        series = TimeSeries('foo.bar',
                            stop - timespan,
                            stop,
                            step,
                            [x**1.5 for x in range(0, timespan, step)])
        series[10] = None
        series.pathExpression = 'foo.bar'
        self.write_series(series, [(100, timespan)])

        ctx = {'startTime': parseATTime('-1d'),
               'endTime': parseATTime('now')}
        stack = functions.timeStack(ctx, [series], '1d', 0, 7)
        self.assertEqual(len(stack), 7)

        stack = functions.timeStack(ctx, [series], '-1d', 0, 7)
        self.assertEqual(len(stack), 7)

    def test_time_shift(self):
        timespan = 3600 * 24 * 8  # 8 days
        stop = int(time.time())
        step = 100
        series = TimeSeries('foo.bar',
                            stop - timespan,
                            stop,
                            step,
                            [x**1.5 for x in range(0, timespan, step)])
        series[10] = None
        series.pathExpression = 'foo.bar'
        self.write_series(series, [(100, timespan)])

        ctx = {'startTime': parseATTime('-1d'),
               'endTime': parseATTime('now')}
        shift = functions.timeShift(ctx, [series], '1d')
        self.assertEqual(len(shift), 1)

        shift = functions.timeShift(ctx, [series], '-1d', False)
        self.assertEqual(len(shift), 1)

        shift = functions.timeShift(ctx, [], '-1d')
        self.assertEqual(len(shift), 0)

    def test_constant_line(self):
        ctx = {
            'startTime': parseATTime('-1d'),
            'endTime': parseATTime('now'),
        }
        line = functions.constantLine(ctx, 12)[0]
        self.assertEqual(list(line), [12, 12, 12])
        self.assertEqual(line.step, 3600 * 24 // 2)

    def test_aggregate_line(self):
        ctx = {
            'startTime': parseATTime('-1d'),
            'endTime': parseATTime('now'),
        }
        series = self._generate_series_list(config=[range(100)])
        line = functions.aggregateLine(ctx, series)[0]
        self.assertEqual(list(line), [49.5, 49.5, 49.5])

        line = functions.aggregateLine(ctx, series, 'avg')[0]
        self.assertEqual(list(line), [49.5, 49.5, 49.5])

        line = functions.aggregateLine(ctx, series, 'min')[0]
        self.assertEqual(list(line), [0, 0, 0])

        line = functions.aggregateLine(ctx, series, 'max')[0]
        self.assertEqual(list(line), [99, 99, 99])

        with self.assertRaises(ValueError):
            functions.aggregateLine(ctx, series, 'foo')

    def test_threshold(self):
        ctx = {
            'startTime': parseATTime('-1d'),
            'endTime': parseATTime('now'),
        }
        threshold = functions.threshold(ctx, 123, 'foobar')[0]
        self.assertEqual(list(threshold), [123, 123, 123])

        threshold = functions.threshold(ctx, 123)[0]
        self.assertEqual(list(threshold), [123, 123, 123])

        threshold = functions.threshold(ctx, 123, 'foo', 'red')[0]
        self.assertEqual(list(threshold), [123, 123, 123])
        self.assertEqual(threshold.color, 'red')

    def test_non_null(self):
        one = [None, 0, 2, 3] * 25
        two = [None, 3, 1] * 33 + [None]
        series = self._generate_series_list(config=[one, two])
        non_null = functions.isNonNull({}, series)
        self.assertEqual(non_null[0][:5], [0, 1, 1, 1, 0])
        self.assertEqual(non_null[1][:5], [0, 1, 1, 0, 1])

    def test_identity(self):
        ctx = {
            'startTime': parseATTime('-1d'),
            'endTime': parseATTime('now'),
        }
        identity = functions.identity(ctx, 'foo')[0]
        self.assertEqual(identity.end - identity.start, 3600 * 24)

    def test_count(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(100, 200)])
        count = functions.countSeries({}, series)[0]
        self.assertEqual(list(count), [2] * 100)

    def test_empty_count(self):
        expectedResult = [
            TimeSeries('0', 0, 600, 300, [0, 0, 0]),
        ]
        ctx = {
            'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
            'endTime': datetime(1970, 1, 1, 0, 10, 0, 0, pytz.utc),
        }
        result = functions.countSeries(ctx)
        self.assertEqual(result, expectedResult)

    def test_group_by_node(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(100, 200)])
        grouped = functions.groupByNode({}, series, 1, 'sumSeries')
        first, second = grouped
        self.assertEqual(first.name, 'test-db1')
        self.assertEqual(second.name, 'test-db2')

        series[1].name = series[0].name
        grouped = functions.groupByNode({}, series, 1, 'sumSeries')
        self.assertEqual(len(grouped), 1)
        self.assertEqual(grouped[0].name, 'test-db1')
        self.assertEqual(list(grouped[0])[:3], [100, 102, 104])

    def test_group_by_nodes(self):
        seriesList = [
            TimeSeries('group1.server1.load5', 0, 2, 1, [10, 20]),
            TimeSeries('group1.server1.load10', 0, 2, 1, [1, 2]),
            TimeSeries('group1.server2.load5', 0, 2, 1, [30, 40]),
            TimeSeries('group1.server2.load10', 0, 2, 1, [3, 4]),
            TimeSeries('group2.server1.load5', 0, 2, 1, [40, 50]),
            TimeSeries('group2.server1.load10', 0, 2, 1, [4, 5]),
            TimeSeries('group2.server2.load5', 0, 2, 1, [60, 70]),
            TimeSeries('group2.server2.load10', 0, 2, 1, [6, 7]),
        ]
        for series in seriesList:
            series.pathExpression = series.name
        grouped = functions.groupByNodes({}, seriesList,
                                         'sumSeries', 0, 2)

        expectedNames = ['group1.load5', 'group1.load10',
                         'group2.load5', 'group2.load10']
        self.assertEqual([s.name for s in grouped], expectedNames)

        group1_load10 = grouped[1]
        self.assertEqual(list(group1_load10), [4, 6])

    def test_exclude(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(100, 200)])
        excl = functions.exclude({}, series, 'db1')
        self.assertEqual(excl, [series[1]])

    def test_grep(self):
        series = self._generate_series_list(config=[range(100),
                                                    range(100, 200)])
        grep = functions.grep({}, series, 'db1')
        self.assertEqual(grep, [series[0]])

    def test_smart_summarize(self):
        ctx = {
            'startTime': parseATTime('-1min'),
            'endTime': parseATTime('now'),
            'tzinfo': pytz.timezone('UTC'),
        }
        series = self._generate_series_list(config=[range(100)])
        for s in series:
            self.write_series(s)
        summ = functions.smartSummarize(ctx, series, '5s')[0]
        self.assertEqual(summ[:3], [220, 245, 270])

        summ = functions.smartSummarize(ctx, series, '5s', 'avg')[0]
        self.assertEqual(summ[:3], [44, 49, 54])

        summ = functions.smartSummarize(ctx, series, '5s', 'last')[0]
        self.assertEqual(summ[:3], [46, 51, 56])

        summ = functions.smartSummarize(ctx, series, '5s', 'max')[0]
        self.assertEqual(summ[:3], [46, 51, 56])

        summ = functions.smartSummarize(ctx, series, '5s', 'min')[0]
        self.assertEqual(summ[:3], [42, 47, 52])

        # Higher time interval should not trigger timezone errors
        functions.smartSummarize(ctx, series, '100s', 'min')[0]

    def test_summarize(self):
        series = self._generate_series_list(config=[list(range(99)) + [None]])

        # summarize is not consistent enough to allow testing exact output
        functions.summarize({}, series, '5s')[0]
        functions.summarize({}, series, '5s', 'avg', True)[0]
        functions.summarize({}, series, '5s', 'last')[0]
        functions.summarize({}, series, '5s', 'min')[0]
        functions.summarize({}, series, '5s', 'max')[0]

    def test_hitcount(self):
        ctx = {
            'startTime': parseATTime('-1min'),
            'endTime': parseATTime('now'),
            'tzinfo': pytz.timezone('UTC'),
        }
        series = self._generate_series_list(config=[list(range(99)) + [None]])
        for s in series:
            self.write_series(s)

        hit = functions.hitcount(ctx, series, '5s')[0]
        self.assertEqual(hit[:3], [0, 15, 40])

        hit = functions.hitcount(ctx, series, '5s', True)[0]
        self.assertEqual(hit[:3], [220, 245, 270])

        try:
            hit = functions.hitcount(ctx, series, '1min', True)[0]
            hit = functions.hitcount(ctx, series, '1h', True)[0]
            hit = functions.hitcount(ctx, series, '1d', True)[0]
        except ValueError as e:
            self.fail("hitcount() raised ValueError: %s" % str(e))

    def test_random_walk(self):
        ctx = {
            'startTime': parseATTime('-12h'),
            'endTime': parseATTime('now'),
        }
        walk = functions.randomWalkFunction(ctx, 'foo')[0]
        self.assertEqual(len(walk), 721)

    def test_null_zero_sum(self):
        s = TimeSeries("s", 0, 1, 1, [None])
        s.pathExpression = 's'
        [series] = functions.sumSeries({}, [s])
        self.assertEqual(list(series), [None])

        s = TimeSeries("s", 0, 1, 1, [None, 1])
        s.pathExpression = 's'
        t = TimeSeries("s", 0, 1, 1, [None, None])
        t.pathExpression = 't'
        [series] = functions.sumSeries({}, [s, t])
        self.assertEqual(list(series), [None, 1])

    def test_multiply_with_wildcards(self):
        s1 = [
            TimeSeries('web.host-1.avg-response.value', 0, 1, 1, [1, 10, 11]),
            TimeSeries('web.host-2.avg-response.value', 0, 1, 1, [2, 20, 21]),
            TimeSeries('web.host-3.avg-response.value', 0, 1, 1, [3, 30, 31]),
            TimeSeries('web.host-4.avg-response.value', 0, 1, 1, [4, 40, 41]),
        ]
        s2 = [
            TimeSeries('web.host-4.total-request.value', 0, 1, 1, [4, 8, 12]),
            TimeSeries('web.host-3.total-request.value', 0, 1, 1, [3, 7, 11]),
            TimeSeries('web.host-1.total-request.value', 0, 1, 1, [1, 5, 9]),
            TimeSeries('web.host-2.total-request.value', 0, 1, 1, [2, 6, 10]),
        ]
        expected = [
            TimeSeries('web.host-1', 0, 1, 1, [1, 50, 99]),
            TimeSeries('web.host-2', 0, 1, 1, [4, 120, 210]),
            TimeSeries('web.host-3', 0, 1, 1, [9, 210, 341]),
            TimeSeries('web.host-4', 0, 1, 1, [16, 320, 492]),
        ]
        results = functions.multiplySeriesWithWildcards({}, s1 + s2, 2, 3)
        self.assertEqual(results, expected)

    def test_timeslice(self):
        series = [
            TimeSeries('test.value', 0, 600, 60,
                       [None, 1, 2, 3, None, 5, 6, None, 7, 8, 9]),
        ]

        expected = [
            TimeSeries('timeSlice(test.value, 180, 480)', 0, 600, 60,
                       [None, None, None, 3, None, 5, 6, None, 7, None, None]),
        ]

        results = functions.timeSlice({
            'startTime': datetime(1970, 1, 1, 0, 0, 0, 0, pytz.utc),
            'endTime': datetime(1970, 1, 1, 0, 9, 0, 0, pytz.utc),
            'data': [],
        }, series, '00:03 19700101', '00:08 19700101')
        self.assertEqual(results, expected)

    def test_remove_emtpy(self):
        series = [
            TimeSeries('foo.bar', 0, 100, 10,
                       [None, None, None, 0, 0, 0, 1, 1, 1, None]),
            TimeSeries('foo.baz', 0, 100, 10, [None] * 10),
            TimeSeries('foo.blah', 0, 100, 10,
                       [None, None, None, 0, 0, 0, 0, 0, 0, None]),
        ]

        results = functions.removeEmptySeries({}, series)
        self.assertEqual(results, [series[0], series[2]])

    def test_legend_value_with_system_preserves_sign(self):
        series = [TimeSeries("foo", 0, 1, 1, [-10000, -20000, -30000, -40000])]
        [result] = functions.legendValue({}, series, "avg", "si")
        self.assertEqual(result.name, "foo                 avg  -25.00K   ")

    def test_linear_regression(self):
        now = int(time.time())
        now -= now % 60

        # savedSeries would be eg: ('test.value', 180, 480, 60)
        savedStart = now - 1320
        savedEnd = now - 1020
        savedSeries = TimeSeries('test.value', savedStart, savedEnd, 60,
                                 [3, None, 5, 6, None, 8])
        savedSeries.pathExpression = 'test.value'
        self.write_series(savedSeries, [(60, 60)])

        # inputSeries would be eg: ('test.value', 1200, 1500, 60)
        inputStart = now - 300
        inputSeries = TimeSeries('test.value', inputStart, now, 60,
                                 [123, None, None, 456, None, None, None])
        inputSeries.pathExpression = 'test.value'

        results = functions.linearRegression({
            'startTime': parseATTime(str(inputStart)),
        }, [inputSeries], str(savedStart), str(savedEnd))

        expected = [
            TimeSeries('linearRegression(test.value, %s, %s)' %
                       (savedStart, savedEnd), inputStart, now, 60,
                       [20.0, 21.0, 22.0, 23.0, 24.0, 25.0, 26.0])
        ]

        # regression function calculated from datapoints on minutes 3 to 8
        self.assertEqual(results, expected)

    def test_apply_by_node(self):
        end = int(time.time())
        start = end - 3

        seriesList = [
            TimeSeries('servers.s1.disk.bytes_used',
                       start, end, 1, [10, 20, 30]),
            TimeSeries('servers.s1.disk.bytes_free',
                       start, end, 1, [90, 80, 70]),
            TimeSeries('servers.s2.disk.bytes_used',
                       start, end, 1, [1, 2, 3]),
            TimeSeries('servers.s2.disk.bytes_free',
                       start, end, 1, [99, 98, 97])
        ]
        for series in seriesList:
            series.pathExpression = series.name
            self.write_series(series)

        expectedResults = [
            TimeSeries('servers.s1.disk.pct_used',
                       start, end, 1, [0.10, 0.20, 0.30]),
            TimeSeries('servers.s2.disk.pct_used', start, end, 1,
                       [0.01, 0.02, 0.03])
        ]

        result = functions.applyByNode({
                'startTime': parseATTime(str(start - 1)),
                'endTime': parseATTime(str(end - 1)),
            }, seriesList, 1,
            'divideSeries(%.disk.bytes_used, sumSeries(%.disk.bytes_*))',
            '%.disk.pct_used')
        self.assertEqual(result, expectedResults)
