from __future__ import absolute_import

import os
import re

import rrdtool

from ..node import BranchNode
from ..node import LeafNode
from ..intervals import Interval
from ..intervals import IntervalSet
from . import match_entries


search_ds_name = re.compile('^ds\[(.*?)\]\.index$').search
search_rra_index = re.compile('^rra\[(.*?)\].pdp_per_row$').search


class RRDToolFinder(object):
    def __init__(self, config):
        self.directory = config['rrdtool']['directory']

    def find_nodes(self, query):
        patterns = query.pattern.split('.')
        return self._find_nodes(self.directory, patterns, '')

    def _find_nodes(self, parent_dir, patterns, parent_metric):
        pattern = patterns[0]
        patterns = patterns[1:]

        for mtype, full_path, metric in self._yield_metrics(parent_dir):
            if not self._match(metric, pattern):
                continue

            if parent_metric:
                metric = "%s.%s" % (parent_metric, metric)

            if mtype == 'directory':
                if not patterns:
                    yield BranchNode(metric)
                else:
                    for node in self._find_nodes(full_path, patterns, metric):
                        yield node

            elif mtype == 'rrd_file':
                for node in self._nodes_from_rrd(full_path, patterns, metric):
                    yield node

    def _yield_metrics(self, directory):
        for name in os.listdir(directory):
            full_path = os.path.join(directory, name)

            if os.path.isdir(full_path):
                yield 'directory', full_path, name.replace('.', '_')

            elif os.path.isfile(full_path) and name.endswith('.rrd'):
                yield 'rrd_file', full_path, name[:-4].replace('.', '_')

    def _nodes_from_rrd(self, full_path, patterns, metric):
        if not patterns:
            yield BranchNode(metric)
        else:
            dss = self._get_dss(full_path)
            if len(dss) == 1:
                it = self._nodes_from_single_ds_rrd(
                    full_path,
                    patterns,
                    metric,
                    dss)
            else:
                it = self._nodes_from_multi_ds_rrd(
                    full_path,
                    patterns,
                    metric,
                    dss)

            for node in it:
                yield node

    def _nodes_from_single_ds_rrd(self, full_path, patterns, metric, dss):
        for node in self._nodes_from_rra(full_path, patterns, metric, dss[0]):
            yield node

    def _nodes_from_multi_ds_rrd(self, full_path, patterns, metric, dss):
        pattern = patterns[0]
        patterns = patterns[1:]
        for ds in dss:
            if not self._match(ds, pattern):
                continue

            new_metric = "%s.%s" % (metric, ds)
            if not patterns:
                yield BranchNode(new_metric)
            else:
                it = self._nodes_from_rra(full_path, patterns, new_metric, ds)
                for node in it:
                    yield node

    def _nodes_from_rra(self, full_path, patterns, parent_metric, ds):
        assert len(patterns) == 1
        for cf in self._get_cfs(full_path):
            if not self._match(cf, patterns[0]):
                continue

            reader = Reader(full_path, ds, cf)
            yield LeafNode("%s.%s" % (parent_metric, cf), reader)

    def _get_dss(self, rrdfull_path):
        rrd_info = rrdtool.info(rrdfull_path)
        dss = (search_ds_name(key) for key in rrd_info)
        return list({match.group(1) for match in dss if match})

    def _get_cfs(self, rrdfull_path):
        rrd_info = rrdtool.info(rrdfull_path)
        return list({rra['cf'] for rra in _yield_rras(rrd_info)})

    def _match(self, metric, pattern):
        return match_entries([metric], pattern)


class Reader(object):
    def __init__(self, path, ds, cf):
        self.path = path
        self.ds = ds
        self.cf = cf

    def fetch(self, start, end):
        args = [
            self.path,
            self.cf,
            '--start',
            str(int(start)),
            '--end',
            str(int(end))
        ]

        val_range, values, data = rrdtool.fetch(*args)
        index = values.index(self.ds)
        data = [row[index] for row in data]
        return (val_range, data)

    def get_intervals(self):
        return IntervalSet(list(self._yield_intervals()))

    def _yield_intervals(self):
        rrd_info = rrdtool.info(self.path)
        step = rrd_info['step']
        last_update = rrd_info['last_update']

        for rra in _yield_rras(rrd_info):
            if rra['cf'] != self.cf:
                continue

            yield Interval(last_update - (step * rra['steps']), last_update)

def _yield_rras(rrd_info):
    for key in rrd_info:
        match = search_rra_index(key)
        if not match:
            continue

        yield {
            'steps': rrd_info[match.group(0)],
            'cf': rrd_info['rra[%s].cf' % match.group(1)]
        }
