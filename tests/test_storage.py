import time

from graphite_api.storage import FindQuery

from . import TestCase


class StorageTestCase(TestCase):
    def test_find_query(self):
        end = int(time.time())
        start = end - 3600

        query = FindQuery('collectd', None, None)
        self.assertEqual(repr(query), '<FindQuery: collectd from * until *>')

        query = FindQuery('collectd', start, None)
        self.assertEqual(repr(query), '<FindQuery: collectd from %s until *>'
                         % time.ctime(start))

        query = FindQuery('collectd', None, end)
        self.assertEqual(repr(query), '<FindQuery: collectd from * until %s>'
                         % time.ctime(end))
