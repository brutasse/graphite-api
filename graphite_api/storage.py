import time

from collections import defaultdict

from .utils import is_pattern
from .node import LeafNode
from .intervals import Interval
from .readers import MultiReader


class Store(object):
    def __init__(self, finders=None):
        self.finders = finders

    def find(self, pattern, startTime=None, endTime=None, local=True):
        query = FindQuery(pattern, startTime, endTime)

        matching_nodes = set()

        # Search locally
        for finder in self.finders:
            for node in finder.find_nodes(query):
                matching_nodes.add(node)

        # Group matching nodes by their path
        nodes_by_path = defaultdict(list)
        for node in matching_nodes:
            nodes_by_path[node.path].append(node)

        # Reduce matching nodes for each path to a minimal set
        found_branch_nodes = set()

        for path, nodes in sorted(nodes_by_path.items(), key=lambda k: k[0]):
            leaf_nodes = set()

            # First we dispense with the BranchNodes
            for node in nodes:
                if node.is_leaf:
                    leaf_nodes.add(node)
                elif node.path not in found_branch_nodes:
                    # TODO need to filter branch nodes based on requested
                    # interval... how?!?!?
                    yield node
                    found_branch_nodes.add(node.path)

            if not leaf_nodes:
                continue

            if len(leaf_nodes) == 1:
                yield leaf_nodes.pop()
            elif len(leaf_nodes) > 1:
                reader = MultiReader(leaf_nodes)
                yield LeafNode(path, reader)


class FindQuery(object):
    def __init__(self, pattern, startTime, endTime):
        self.pattern = pattern
        self.startTime = startTime
        self.endTime = endTime
        self.isExact = is_pattern(pattern)
        self.interval = Interval(
            float('-inf') if startTime is None else startTime,
            float('inf') if endTime is None else endTime)

    def __repr__(self):
        if self.startTime is None:
            startString = '*'
        else:
            startString = time.ctime(self.startTime)

        if self.endTime is None:
            endString = '*'
        else:
            endString = time.ctime(self.endTime)

        return '<FindQuery: %s from %s until %s>' % (self.pattern, startString,
                                                     endString)
