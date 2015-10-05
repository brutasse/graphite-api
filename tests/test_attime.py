import datetime
import time
import pytz

from graphite_api.render.attime import parseATTime

from . import TestCase


class AtTestCase(TestCase):
    default_tz = pytz.utc
    specified_tz = pytz.timezone('America/Los_Angeles')

    def test_absolute_time(self):
        time_string = '12:0020150308'
        expected_time = self.default_tz.localize(
            datetime.datetime.strptime(time_string, '%H:%M%Y%m%d'))
        actual_time = parseATTime(time_string)
        self.assertEqual(actual_time, expected_time)

        expected_time = self.specified_tz.localize(
            datetime.datetime.strptime(time_string, '%H:%M%Y%m%d'))
        actual_time = parseATTime(time_string, self.specified_tz)
        self.assertEqual(actual_time, expected_time)

    def test_parse(self):
        for value in [
            str(int(time.time())),
            '20140319',
            '20130319+1y',
            '20130319+1mon',
            '20130319+1w',
            '12:12_20130319',
            '3:05am_20130319',
            '3:05pm_20130319',
            'noon20130319',
            'midnight20130319',
            'teatime20130319',
            'yesterday',
            'tomorrow',
            '03/19/2014',
            '03/19/1800',
            '03/19/1950',
            'feb 27',
            'mar 5',
            'mon',
            'tue',
            'wed',
            'thu',
            'fri',
            'sat',
            'sun',
            '10:00',
        ]:
            self.assertIsInstance(parseATTime(value), datetime.datetime)

        for value in [
            '20130319+1foo',
            'mar',
            'wat',
        ]:
            with self.assertRaises(Exception):
                parseATTime(value)
