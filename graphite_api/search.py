import time
import os.path

from structlog import get_logger

from .finders import match_entries
from .utils import is_pattern

logger = get_logger()


class IndexSearcher(object):
    def __init__(self, index_path):
        self.log = logger.bind(index_path=index_path)
        self.index_path = index_path
        self.last_mtime = 0
        self._tree = (None, {})  # (data, children)
        self.reload()

    @property
    def tree(self):
        current_mtime = os.path.getmtime(self.index_path)
        if current_mtime > self.last_mtime:
            self.log.info('reloading stale index',
                          current_mtime=current_mtime,
                          last_mtime=self.last_mtime)
            self.reload()

        return self._tree

    def reload(self):
        self.log.info("reading index data")
        if not os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'w'):
                    pass
            except IOError as e:
                self.log.error("error writing search index",
                               path=self.index_path, error=str(e))
                self._tree = (None, {})
                return
        t = time.time()
        total_entries = 0
        tree = (None, {})  # (data, children)
        with open(self.index_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                branches = line.split('.')
                leaf = branches.pop()
                cursor = tree
                for branch in branches:
                    if branch not in cursor[1]:
                        cursor[1][branch] = (None, {})  # (data, children)
                    cursor = cursor[1][branch]

                cursor[1][leaf] = (line, {})
                total_entries += 1

        self._tree = tree
        self.last_mtime = os.path.getmtime(self.index_path)
        self.log.info("search index reloaded", total_entries=total_entries,
                      duration=time.time() - t)

    def search(self, query, max_results=None, keep_query_pattern=False):
        query_parts = query.split('.')
        metrics_found = set()
        for result in self.subtree_query(self.tree, query_parts):
            if result['path'] in metrics_found:
                continue
            yield result

            metrics_found.add(result['path'])
            if max_results is not None and len(metrics_found) >= max_results:
                return

    def subtree_query(self, root, query_parts):
        if query_parts:
            my_query = query_parts[0]
            if is_pattern(my_query):
                matches = [root[1][node] for node in match_entries(root[1],
                                                                   my_query)]
            elif my_query in root[1]:
                matches = [root[1][my_query]]
            else:
                matches = []

        else:
            matches = root[1].values()

        for child_node in matches:
            result = {
                'path': child_node[0],
                'is_leaf': bool(child_node[0]),
            }
            if result['path'] is not None and not result['is_leaf']:
                result['path'] += '.'
            yield result

            if query_parts:
                for result in self.subtree_query(child_node, query_parts[1:]):
                    yield result
