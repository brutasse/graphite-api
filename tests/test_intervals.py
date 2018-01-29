from influxgraph_graphite_api.intervals import Interval, IntervalSet, union_overlapping

from . import TestCase


class IntervalTestCase(TestCase):
    def test_interval(self):
        with self.assertRaises(ValueError):
            Interval(1, 0)

        i = Interval(0, 1)
        j = Interval(1, 2)
        k = Interval(0, 1)
        l = Interval(0, 0)
        self.assertNotEqual(i, j)
        self.assertEqual(i, k)
        self.assertEqual(hash(i), hash(k))

        with self.assertRaises(TypeError):
            len(i)

        self.assertTrue(j > i)

        self.assertTrue(i)
        self.assertFalse(l)

        self.assertEqual(repr(i), '<Interval: (0, 1)>')

        self.assertIsNone(i.intersect(j))
        self.assertEqual(i.intersect(k), k)
        self.assertTrue(i.overlaps(j))
        self.assertEqual(i.union(j), Interval(0, 2))

        with self.assertRaises(TypeError):
            j.union(l)

        self.assertEqual(union_overlapping([i, j, k, l]),
                         [Interval(0, 2)])

    def test_interval_set(self):
        i = Interval(0, 1)
        j = Interval(1, 2)

        s = IntervalSet([i, j])
        self.assertEqual(repr(s), '[<Interval: (0, 2)>]')
        s = IntervalSet([i, j], disjoint=True)

        it = iter(s)
        self.assertEqual(next(it), i)
        self.assertEqual(next(it), j)

        self.assertTrue(s)
        self.assertFalse(IntervalSet([]))

        self.assertEqual(s - IntervalSet([i]),
                         IntervalSet([j]))

        self.assertFalse(IntervalSet([]).intersect(s))

        self.assertEqual(s.union(IntervalSet([Interval(3, 4)])),
                         IntervalSet([Interval(3, 4), i, j]))
