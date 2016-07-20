import struct
from six.moves import cPickle as pickle

try:
    from unittest.mock import patch
except ImportError:
    from mock import patch

from graphite_api import carbonlink
from graphite_api.carbonlink import ConsistentHashRing, CarbonLinkPool

from . import TestCase


class CarbonLinkTestCase(TestCase):
    def test_allowed_modules(self):
        with self.assertRaises(pickle.UnpicklingError) as context:
            carbonlink.allowed_module('foo', 'bar')
        self.assertIn('Attempting to unpickle unsafe module foo',
                      str(context.exception))

        with self.assertRaises(pickle.UnpicklingError) as context:
            carbonlink.allowed_module('__builtin__', 'bar')
        self.assertIn('Attempting to unpickle unsafe class bar',
                      str(context.exception))

        self.assertIsNotNone(carbonlink.allowed_module('collections', 'deque'))
        self.assertIsNotNone(carbonlink.allowed_module('__builtin__', 'list'))


class ConsistentHashRingTest(TestCase):
    def test_chr_compute_ring_position(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        self.assertEqual(hashring.compute_ring_position('hosts.worker1.cpu'),
                         64833)
        self.assertEqual(hashring.compute_ring_position('hosts.worker2.cpu'),
                         38509)

    def test_chr_add_node(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        self.assertEqual(hashring.nodes, set(hosts))
        hashring.add_node(("127.0.0.1", "cache3"))
        hosts.insert(0, ("127.0.0.1", "cache3"))
        self.assertEqual(hashring.nodes, set(hosts))
        self.assertEqual(hashring.nodes_len, 4)

    def test_chr_add_node_duplicate(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        self.assertEqual(hashring.nodes, set(hosts))
        hashring.add_node(("127.0.0.1", "cache2"))
        self.assertEqual(hashring.nodes, set(hosts))
        self.assertEqual(hashring.nodes_len, 3)

    def test_chr_remove_node(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        self.assertEqual(hashring.nodes, set(hosts))
        hashring.remove_node(("127.0.0.1", "cache2"))
        hosts.pop()
        self.assertEqual(hashring.nodes, set(hosts))
        self.assertEqual(hashring.nodes_len, 2)

    def test_chr_remove_node_missing(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        self.assertEqual(hashring.nodes, set(hosts))
        hashring.remove_node(("127.0.0.1", "cache4"))
        self.assertEqual(hashring.nodes, set(hosts))
        self.assertEqual(hashring.nodes_len, 3)

    def test_chr_get_node(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        node = hashring.get_node('hosts.worker1.cpu')
        self.assertEqual(node, ('127.0.0.1', 'cache2'))

    def test_chr_get_nodes(self):
        hosts = [
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
            ("127.0.0.1", "cache2"),
        ]
        hashring = ConsistentHashRing(hosts)
        node = hashring.get_nodes('hosts.worker1.cpu')
        expected = [
            ("127.0.0.1", "cache2"),
            ("127.0.0.1", "cache0"),
            ("127.0.0.1", "cache1"),
        ]
        self.assertEqual(node, expected)


class CarbonLinkPoolTest(TestCase):
    def test_clp_replication_factor(self):
        with self.assertRaises(Exception) as context:
            CarbonLinkPool(['127.0.0.1:2003'], replication_factor=2)
        self.assertIn('replication_factor=2 cannot exceed servers=1',
                      str(context.exception))

    def test_clp_requests(self):
        hosts = [
            '192.168.0.1:2003:cache0',
            '192.168.0.2:2003:cache1',
            '192.168.0.3:2003:cache2',
        ]
        carbonlink = CarbonLinkPool(hosts, replication_factor=3)

        with patch('socket.socket'):
            for host in hosts:
                server, port, instance = host.split(':')
                conn = carbonlink.get_connection((server, instance))
                conn.connect.assert_called_with((server, int(port)))
                carbonlink.connections[(server, instance)].add(conn)

        def mock_recv_query(size):
            data = pickle.dumps(dict(datapoints=[1, 2, 3]))
            if size == 4:
                return struct.pack('!I', len(data))
            elif size == len(data):
                return data
            else:
                raise ValueError('unexpected size %s' % size)

        conn.recv.side_effect = mock_recv_query
        datapoints = carbonlink.query('hosts.worker1.cpu')
        self.assertEqual(datapoints, [1, 2, 3])

        datapoints = carbonlink.query('carbon.send_to_all.request')
        self.assertEqual(datapoints, [1, 2, 3] * 3)

        def mock_recv_get_metadata(size):
            data = pickle.dumps(dict(value='foo'))
            if size == 4:
                return struct.pack('!I', len(data))
            elif size == len(data):
                return data
            else:
                raise ValueError('unexpected size %s' % size)

        conn.recv.side_effect = mock_recv_get_metadata
        metadata = carbonlink.get_metadata('hosts.worker1.cpu', 'key')
        self.assertEqual(metadata, 'foo')

        def mock_recv_set_metadata(size):
            data = pickle.dumps(dict(old_value='foo', new_value='bar'))
            if size == 4:
                return struct.pack('!I', len(data))
            elif size == len(data):
                return data
            else:
                raise ValueError('unexpected size %s' % size)

        conn.recv.side_effect = mock_recv_set_metadata
        results = carbonlink.set_metadata('hosts.worker1.cpu', 'foo', 'bar')
        self.assertEqual(results, {'old_value': 'foo', 'new_value': 'bar'})
