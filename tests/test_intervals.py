from graphite_api.intervals import Interval, IntervalSet, union_overlapping

from . import TestCase


class IntervalTestCase(TestCase):
    def test_interval(self):
        with self.assertRaises(ValueError):
            Interval(1, 0)

        a = Interval(0, 1)
        b = Interval(1, 2)
        c = Interval(0, 1)
        d = Interval(0, 0)
        self.assertNotEqual(a, b)
        self.assertEqual(a, c)
        self.assertEqual(hash(a), hash(c))

        with self.assertRaises(TypeError):
            len(a)

        self.assertTrue(b > a)

        self.assertTrue(a)
        self.assertFalse(d)

        self.assertEqual(repr(a), '<Interval: (0, 1)>')

        self.assertIsNone(a.intersect(b))
        self.assertEqual(a.intersect(c), c)
        self.assertTrue(a.overlaps(b))
        self.assertEqual(a.union(b), Interval(0, 2))

        with self.assertRaises(TypeError):
            b.union(d)

        self.assertEqual(union_overlapping([a, b, c, d]),
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
