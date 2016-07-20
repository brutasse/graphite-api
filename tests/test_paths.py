from . import TestCase
from graphite_api.app import pathsFromTarget


class PathsTest(TestCase):
    """
    TestCase for pathsFromTarget function

    """
    def validate_paths(self, expected, test):
        """
        Assert the lengths of the expected list and the test list are the same
        Also assert that every member of the expected list is present in the
            test list.

        """
        # Check that test is a list
        self.assertTrue(isinstance(test, list))
        # Check length before converting to sets
        self.assertEqual(len(expected), len(test))
        # Convert lists to sets and verify equality
        self.assertEqual(set(expected), set(test))

    def test_simple(self):
        """
        Tests a target containing a single path expression.

        """
        target = 'test.simple.metric'
        expected = [target]
        self.validate_paths(expected, pathsFromTarget({}, target))

    def test_func_args(self):
        """
        Tests a target containing function call with path expressions as
        arguments.

        """
        path_1 = 'test.1.metric'
        path_2 = 'test.2.metric'
        target = 'sumSeries(%s,%s)' % (path_1, path_2)
        expected = [path_1, path_2]
        self.validate_paths(expected, pathsFromTarget({}, target))

    def test_func_kwargs(self):
        """
        Tests a target containing a function call with path expressions as
        a kwarg.

        """
        path_a = 'test.a.metric'
        path_b = 'test.b.metric'
        target = 'someFunc(%s,b=%s)' % (path_a, path_b)
        expected = [path_a, path_b]
        self.validate_paths(expected, pathsFromTarget({}, target))

    def test_func_nested(self):
        """
        Tests a target containing nested functions with a mix of args and
        kwargs.

        """
        paths = (
            'test.a.metric',
            'test.b.metric',
            'test.c.metric',
            'test.d.metric',
        )
        target = 'outerFunc(innerFunc(%s, %s), s=innerFunc(%s, %s))' % paths
        expected = list(paths)
        self.validate_paths(expected, pathsFromTarget({}, target))
