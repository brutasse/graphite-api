import bisect
import errno
import random
import socket
import struct
import time

from hashlib import md5
from io import BytesIO
from importlib import import_module
from select import select

import six
from six.moves import cPickle as pickle  # noqa
from structlog import get_logger

logger = get_logger()

pickle_safe = {
    'copy_reg': set(['_reconstructor']),
    '__builtin__': set(['object', 'list']),
    'collections': set(['deque']),
}
renames = {
    'copy_reg': 'copyreg',
    '__builtin__': 'builtins',
}


def allowed_module(module, name):
    if module not in pickle_safe:
        raise pickle.UnpicklingError(
            'Attempting to unpickle unsafe module %s' % module)
    if name not in pickle_safe[module]:
        raise pickle.UnpicklingError(
            'Attempting to unpickle unsafe class %s' % name)
    if module in renames:
        module = 'six.moves.{0}'.format(renames[module])
    mod = import_module(module)
    return getattr(mod, name)


if six.PY2:
    class SafeUnpickler(object):
        @classmethod
        def find_class(cls, module, name):
            return allowed_module(module, name)

        @classmethod
        def loads(cls, s):
            obj = pickle.Unpickler(BytesIO(s))
            obj.find_global = cls.find_class
            return obj.load()
else:
    class SafeUnpickler(pickle.Unpickler):
        def find_class(self, module, name):
            return allowed_module(module, name)

        @classmethod
        def loads(cls, s):
            obj = SafeUnpickler(BytesIO(s))
            return obj.load()


class ConsistentHashRing(object):
    def __init__(self, nodes, replica_count=100):
        self.ring = []
        self.ring_len = len(self.ring)
        self.nodes = set()
        self.nodes_len = len(self.nodes)
        self.replica_count = replica_count
        for node in nodes:
            self.add_node(node)

    def compute_ring_position(self, key):
        big_hash = md5(str(key).encode()).hexdigest()
        small_hash = int(big_hash[:4], 16)
        return small_hash

    def add_node(self, key):
        self.nodes.add(key)
        self.nodes_len = len(self.nodes)
        for i in range(self.replica_count):
            replica_key = "%s:%d" % (key, i)
            position = self.compute_ring_position(replica_key)
            entry = position, key
            bisect.insort(self.ring, entry)
        self.ring_len = len(self.ring)

    def remove_node(self, key):
        self.nodes.discard(key)
        self.nodes_len = len(self.nodes)
        self.ring = [entry for entry in self.ring if entry[1] != key]
        self.ring_len = len(self.ring)

    def get_node(self, key):
        assert self.ring
        position = self.compute_ring_position(key)
        search_entry = position, None
        index = bisect.bisect_left(self.ring, search_entry) % self.ring_len
        entry = self.ring[index]
        return entry[1]

    def get_nodes(self, key):
        nodes = []
        position = self.compute_ring_position(key)
        search_entry = position, None
        index = bisect.bisect_left(self.ring, search_entry) % self.ring_len
        last_index = (index - 1) % self.ring_len
        nodes_len = len(nodes)
        while nodes_len < self.nodes_len and index != last_index:
            position, next_node = self.ring[index]
            if next_node not in nodes:
                nodes.append(next_node)
                nodes_len += 1
            index = (index + 1) % self.ring_len
        return nodes


class CarbonLinkPool(object):
    def __init__(self, hosts, timeout=1, retry_delay=15,
                 carbon_prefix='carbon', replication_factor=1,
                 hashing_keyfunc=lambda x: x):
        self.carbon_prefix = carbon_prefix
        self.retry_delay = retry_delay
        self.hosts = []
        self.ports = {}
        servers = set()
        for host in hosts:
            parts = host.split(':')
            if len(parts) == 2:
                parts.append(None)
            server, port, instance = parts
            self.hosts.append((server, instance))
            self.ports[(server, instance)] = port
            servers.add(server)

        self.timeout = float(timeout)
        if len(servers) < replication_factor:
            raise Exception(
                "replication_factor=%d cannot exceed servers=%d" % (
                    replication_factor, len(servers)))
        self.replication_factor = replication_factor

        self.hash_ring = ConsistentHashRing(self.hosts)
        self.keyfunc = hashing_keyfunc
        self.connections = {}
        self.last_failure = {}
        # Create a connection pool for each host
        for host in self.hosts:
            self.connections[host] = set()

    def select_host(self, metric):
        """
        Returns the carbon host that has data for the given metric.
        """
        key = self.keyfunc(metric)
        nodes = []
        servers = set()
        for node in self.hash_ring.get_nodes(key):
            server, instance = node
            if server in servers:
                continue
            servers.add(server)
            nodes.append(node)
            if len(servers) >= self.replication_factor:
                break
        available = [n for n in nodes if self.is_available(n)]
        return random.choice(available or nodes)

    def is_available(self, host):
        now = time.time()
        last_fail = self.last_failure.get(host, 0)
        return (now - last_fail) < self.retry_delay

    def get_connection(self, host):
        # First try to take one out of the pool for this host
        server, instance = host
        port = self.ports[host]
        pool = self.connections[host]
        try:
            return pool.pop()
        except KeyError:
            pass  # nothing left in the pool, gotta make a new connection

        logger.info("new carbonlink socket", host=str(host))
        connection = socket.socket()
        connection.settimeout(self.timeout)
        try:
            connection.connect((server, int(port)))
        except:
            self.last_failure[host] = time.time()
            raise
        connection.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        return connection

    def query(self, metric):
        request = dict(type='cache-query', metric=metric)
        results = self.send_request(request)
        logger.debug("carbonlink request returned", metric=metric,
                     datapoints=len(results['datapoints']))
        return results['datapoints']

    def get_metadata(self, metric, key):
        request = dict(type='get-metadata', metric=metric, key=key)
        results = self.send_request(request)
        logger.debug("carbonlink get-metadata request received",
                     metric=metric, key=key)
        return results['value']

    def set_metadata(self, metric, key, value):
        request = dict(type='set-metadata', metric=metric,
                       key=key, value=value)
        results = self.send_request(request)
        logger.debug("carbonlink set-metadata request received",
                     metric=metric, key=key, value=value)
        return results

    def send_request(self, request):
        metric = request['metric']
        serialized_request = pickle.dumps(request, protocol=2)
        len_prefix = struct.pack("!L", len(serialized_request))
        request_packet = len_prefix + serialized_request
        result = {}
        result.setdefault('datapoints', [])

        if metric.startswith(self.carbon_prefix):
            return self.send_request_to_all(request)

        host = self.select_host(metric)
        conn = self.get_connection(host)
        logger.debug("carbonlink request", metric=metric, host=str(host))
        try:
            conn.sendall(request_packet)
            result = self.recv_response(conn)
        except Exception:
            self.last_failure[host] = time.time()
            logger.info("carbonlink exception", exc_info=True, host=str(host))
        else:
            self.connections[host].add(conn)
            if 'error' in result:
                logger.info("carbonlink error", error=result['error'])
                raise CarbonLinkRequestError(result['error'])
            logger.debug("carbonlink finished receiving",
                         metric=metric, host=host)
        return result

    def send_request_to_all(self, request):
        metric = request['metric']
        serialized_request = pickle.dumps(request, protocol=2)
        len_prefix = struct.pack("!L", len(serialized_request))
        request_packet = len_prefix + serialized_request
        results = {}
        results.setdefault('datapoints', [])

        for host in self.hosts:
            conn = self.get_connection(host)
            logger.debug("carbonlink request", metric=metric, host=str(host))
            try:
                conn.sendall(request_packet)
                result = self.recv_response(conn)
            except Exception:
                self.last_failure[host] = time.time()
                logger.info("carbonlink exception", exc_info=True,
                            host=str(host))
            else:
                self.connections[host].add(conn)
                if 'error' in result:
                    logger.info("carbonlink error",
                                host=str(host), error=result['error'])
                else:
                    if len(result['datapoints']) > 1:
                        results['datapoints'].extend(result['datapoints'])
            logger.debug("carbonlink finished receiving",
                         metric=metric, host=str(host))
        return results

    def recv_response(self, conn):
        len_prefix = recv_exactly(conn, 4)
        body_size = struct.unpack("!L", len_prefix)[0]
        body = recv_exactly(conn, body_size)
        return SafeUnpickler.loads(body)


class CarbonLinkRequestError(Exception):
    pass


# Socket helper functions
def still_connected(sock):
    is_readable = select([sock], [], [], 0)[0]
    if is_readable:
        try:
            recv_buf = sock.recv(1, socket.MSG_DONTWAIT | socket.MSG_PEEK)

        except socket.error as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return True
            else:
                raise
        else:
            return bool(recv_buf)

    else:
        return True


def recv_exactly(conn, num_bytes):
    buf = b''
    while len(buf) < num_bytes:
        data = conn.recv(num_bytes - len(buf))
        if not data:
            raise Exception("Connection lost")
        buf += data
    return buf
