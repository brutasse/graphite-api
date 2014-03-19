import datetime
import time

from graphite_api.render.attime import parseATTime

from . import TestCase


class AtTestCase(TestCase):
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
        ]:
            self.assertIsInstance(parseATTime(value), datetime.datetime)

        for value in [
            '20130319+1foo',
            'mar',
            'wat',
        ]:
            with self.assertRaises(Exception):
                parseATTime(value)
