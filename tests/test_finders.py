import os
import random
import time

from . import TestCase, WHISPER_DIR

from graphite_api.app import app
from graphite_api.intervals import Interval, IntervalSet
from graphite_api.node import LeafNode, BranchNode
from graphite_api.storage import Store
from graphite_api._vendor import whisper


class FinderTest(TestCase):
    def test_custom_finder(self):
        store = Store([DummyFinder()])
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

    def test_multi_finder(self):
        store = Store([DummyFinder(), DummyFinder()])
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
    def find_nodes(self, query):
        if query.pattern == 'foo':
            yield BranchNode('foo')

        elif query.pattern == 'bar.*':
            for i in range(10):
                path = 'bar.{0}'.format(i)
                yield LeafNode(path, DummyReader(path))


class WhisperFinderTest(TestCase):
    _listdir_counter = 0
    _original_listdir = os.listdir

    def test_whisper_finder(self):
        for db in (
            ('whisper_finder', 'foo.wsp'),
            ('whisper_finder', 'foo', 'bar', 'baz.wsp'),
            ('whisper_finder', 'bar', 'baz', 'baz.wsp'),
        ):
            db_path = os.path.join(WHISPER_DIR, *db)
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))
            whisper.create(db_path, [(1, 60)])

        def listdir_mock(d):
            self._listdir_counter += 1
            return self._original_listdir(d)

        try:
            os.listdir = listdir_mock
            store = app.config['GRAPHITE']['store']

            self._listdir_counter = 0
            nodes = store.find('whisper_finder.foo')
            self.assertEqual(len(list(nodes)), 2)
            self.assertEqual(self._listdir_counter, 0)

            self._listdir_counter = 0
            nodes = store.find('whisper_finder.foo.bar.baz')
            self.assertEqual(len(list(nodes)), 1)
            self.assertEqual(self._listdir_counter, 0)

            self._listdir_counter = 0
            nodes = store.find('whisper_finder.*.ba?.{baz,foo}')
            self.assertEqual(len(list(nodes)), 2)
            self.assertEqual(self._listdir_counter, 5)

        finally:
            os.listdir = self._original_listdir

    def test_globstar(self):
        store = app.config['GRAPHITE']['store']
        query = "x.**.x"
        hits = ["x.x", "x._.x", "x._._.x"]
        misses = ["x.x.o", "o.x.x", "x._.x._.o", "o._.x._.x"]
        for path in hits + misses:
            db_path = os.path.join(WHISPER_DIR, path.replace(".", os.sep))
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))
            whisper.create(db_path + '.wsp', [(1, 60)])

        paths = [node.path for node in store.find(query, local=True)]
        for hit in hits:
            self.assertIn(hit, paths)
        for miss in misses:
            self.assertNotIn(miss, paths)

    def test_multiple_globstars(self):
        store = app.config['GRAPHITE']['store']
        query = "y.**.y.**.y"
        hits = [
            "y.y.y", "y._.y.y", "y.y._.y", "y._.y._.y",
            "y._._.y.y", "y.y._._.y"
        ]
        misses = [
            "y.o.y", "o.y.y", "y.y.o", "o.y.y.y",  "y.y.y.o",
            "o._.y._.y", "y._.o._.y", "y._.y._.o"
        ]
        for path in hits + misses:
            db_path = os.path.join(WHISPER_DIR, path.replace(".", os.sep))
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))
            whisper.create(db_path + '.wsp', [(1, 60)])

        paths = [node.path for node in store.find(query, local=True)]
        for hit in hits:
            self.assertIn(hit, paths)
        for miss in misses:
            self.assertNotIn(miss, paths)

    def test_terminal_globstar(self):
        store = app.config['GRAPHITE']['store']
        query = "z.**"
        hits = ["z._", "z._._", "z._._._"]
        misses = ["z", "o._", "o.z._", "o._.z"]
        for path in hits + misses:
            db_path = os.path.join(WHISPER_DIR, path.replace(".", os.sep))
            if not os.path.exists(os.path.dirname(db_path)):
                os.makedirs(os.path.dirname(db_path))
            whisper.create(db_path + '.wsp', [(1, 60)])

        paths = [node.path for node in store.find(query, local=True)]
        for hit in hits:
            self.assertIn(hit, paths)
        for miss in misses:
            self.assertNotIn(miss, paths)
