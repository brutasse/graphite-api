from graphite_api.encoders import JSONEncoder

from . import TestCase


class EncoderTestCase(TestCase):
    def test_json_encoder(self):
        encoder = JSONEncoder()

        with self.assertRaises(TypeError):
            encoder.default(object())

        self.assertEqual(encoder.default(dict({1: 2})), {1: 2})
        self.assertEqual(encoder.default(set([4, 5, 6])), [4, 5, 6])
        self.assertEqual(encoder.default(DummyObject()), [7, 8, 9])


class DummyObject(object):
    def tolist(self):
        return list([7, 8, 9])
