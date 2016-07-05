import random
import time

from . import TestCase

from graphite_api.intervals import Interval, IntervalSet
from graphite_api.node import LeafNode, BranchNode
from graphite_api.storage import Store


class FinderTest(TestCase):
    def test_custom_finder(self):
        store = Store([DummyFinder(DummyReader)])
        nodes = list(store.find("foo"))
        self.assertEqual(len(nodes), 1)
        self.assertEqual(nodes[0].path, 'foo')

        nodes = list(store.find('bar.*'))
        self.assertEqual(len(nodes), 10)
        node = nodes[0]
        self.assertEqual(node.path.split('.')[0], 'bar')

        time_info, series = node.fetch(100, 200)
        self.assertEqual(time_info, (100, 200, 10))
        self.assertEqual(len(series), 10)

    def test_aggregating_reader(self):
        store = Store([DummyFinder(DummyAggregatingReader)])
        nodes = list(store.find('bar.*'))
        node = nodes[0]

        time_info, series = node.fetch(100, 200, 12)
        self.assertEqual(time_info, (100, 200, 10))
        self.assertEqual(len(series), 12)


class DummyAggregatingReader(object):
    __aggregating__ = True

    __slots__ = ('path',)

    def __init__(self, path):
        self.path = path

    def fetch(self, start_time, end_time, max_data_points):
        return (start_time, end_time, 10), [
            random.choice([None, 1, 2, 3]) for i in range(max_data_points)
        ]

    def get_intervals(self):
        return IntervalSet([Interval(time.time() - 3600, time.time())])


class DummyReader(object):
    __slots__ = ('path',)

    def __init__(self, path):
        self.path = path

    def fetch(self, start_time, end_time):
        npoints = (end_time - start_time) // 10
        return (start_time, end_time, 10), [
            random.choice([None, 1, 2, 3]) for i in range(npoints)
        ]

    def get_intervals(self):
        return IntervalSet([Interval(time.time() - 3600, time.time())])


class DummyFinder(object):
    def __init__(self, ReaderClass):
        self.ReaderClass = ReaderClass

    def find_nodes(self, query):
        if query.pattern == 'foo':
            yield BranchNode('foo')

        elif query.pattern == 'bar.*':
            for i in range(10):
                path = 'bar.{0}'.format(i)
                yield LeafNode(path, self.ReaderClass(path))
