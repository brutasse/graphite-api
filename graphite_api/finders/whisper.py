from __future__ import absolute_import

import gzip
import os.path
import time

from structlog import get_logger

from ..carbonlink import CarbonLinkPool
from ..intervals import Interval, IntervalSet
from ..node import BranchNode, LeafNode
from .._vendor import whisper

from . import fs_to_metric, get_real_metric_path, match_entries

logger = get_logger()


class WhisperFinder(object):
    def __init__(self, config):
        self.directories = config['whisper']['directories']
        self.carbonlink = None
        if 'carbon' in config:
            self.carbonlink = CarbonLinkPool(**config['carbon'])
        else:
            self.carbonlink = None

    def find_nodes(self, query):
        logger.debug("find_nodes", finder="whisper", start=query.startTime,
                     end=query.endTime, pattern=query.pattern)
        clean_pattern = query.pattern.replace('\\', '')
        pattern_parts = clean_pattern.split('.')

        for root_dir in self.directories:
            if not os.path.isdir(root_dir):
                os.makedirs(root_dir)
            for absolute_path in self._find_paths(root_dir, pattern_parts):
                if os.path.basename(absolute_path).startswith('.'):
                    continue

                relative_path = absolute_path[len(root_dir):].lstrip(os.sep)
                metric_path = fs_to_metric(relative_path)
                real_metric_path = get_real_metric_path(absolute_path,
                                                        metric_path)

                metric_path_parts = metric_path.split('.')
                for field_index in find_escaped_pattern_fields(query.pattern):
                    metric_path_parts[field_index] = pattern_parts[
                        field_index].replace('\\', '')
                metric_path = '.'.join(metric_path_parts)

                # Now we construct and yield an appropriate Node object
                if os.path.isdir(absolute_path):
                    yield BranchNode(metric_path)

                elif os.path.isfile(absolute_path):
                    if absolute_path.endswith('.wsp'):
                        reader = WhisperReader(absolute_path, real_metric_path,
                                               self.carbonlink)
                        yield LeafNode(metric_path, reader)

                    elif absolute_path.endswith('.wsp.gz'):
                        reader = GzippedWhisperReader(absolute_path,
                                                      real_metric_path,
                                                      self.carbonlink)
                        yield LeafNode(metric_path, reader)

    def _find_paths(self, current_dir, patterns):
        """Recursively generates absolute paths whose components
        underneath current_dir match the corresponding pattern in
        patterns"""
        pattern = patterns[0]
        patterns = patterns[1:]
        entries = os.listdir(current_dir)

        subdirs = [e for e in entries
                   if os.path.isdir(os.path.join(current_dir, e))]
        matching_subdirs = match_entries(subdirs, pattern)

        if patterns:  # we've still got more directories to traverse
            for subdir in matching_subdirs:

                absolute_path = os.path.join(current_dir, subdir)
                for match in self._find_paths(absolute_path, patterns):
                    yield match

        else:  # we've got the last pattern
            files = [e for e in entries
                     if os.path.isfile(os.path.join(current_dir, e))]
            matching_files = match_entries(files, pattern + '.*')

            for _basename in matching_files + matching_subdirs:
                yield os.path.join(current_dir, _basename)


class WhisperReader(object):
    __slots__ = ('fs_path', 'real_metric_path', 'carbonlink')

    def __init__(self, fs_path, real_metric_path, carbonlink=None):
        self.fs_path = fs_path
        self.real_metric_path = real_metric_path
        self.carbonlink = carbonlink

    def get_intervals(self):
        start = time.time() - whisper.info(self.fs_path)['maxRetention']
        end = max(os.stat(self.fs_path).st_mtime, start)
        return IntervalSet([Interval(start, end)])

    def fetch(self, startTime, endTime):  # noqa
        logger.debug("fetch", reader="whisper", path=self.fs_path,
                     metric_path=self.real_metric_path,
                     start=startTime, end=endTime)
        data = whisper.fetch(self.fs_path, startTime, endTime)
        if not data:
            return None

        time_info, values = data
        start, end, step = time_info

        if self.carbonlink:
            cached_datapoints = self.carbonlink.query(self.real_metric_path)
            if isinstance(cached_datapoints, dict):
                cached_datapoints = cached_datapoints.items()
            for timestamp, value in sorted(cached_datapoints):
                # filter only to cached datapoints within [start, end)
                if not (timestamp >= start and timestamp < end):
                    continue
                interval = timestamp - (timestamp % step)
                i = int(interval - start) // step
                values[i] = value

        return time_info, values


class GzippedWhisperReader(WhisperReader):
    def get_intervals(self):
        fh = gzip.GzipFile(self.fs_path, 'rb')
        try:
            info = getattr(whisper, '__readHeader')(fh)  # evil, but necessary.
        finally:
            fh.close()

        start = time.time() - info['maxRetention']
        end = max(os.stat(self.fs_path).st_mtime, start)
        return IntervalSet([Interval(start, end)])

    def fetch(self, startTime, endTime):
        logger.debug("fetch", reader="gzip_whisper", path=self.fs_path,
                     metric_path=self.real_metric_path,
                     start=startTime, end=endTime)
        fh = gzip.GzipFile(self.fs_path, 'rb')
        try:
            return whisper.file_fetch(fh, startTime, endTime)
        finally:
            fh.close()


def find_escaped_pattern_fields(pattern_string):
    pattern_parts = pattern_string.split('.')
    for index, part in enumerate(pattern_parts):
        if is_escaped_pattern(part):
            yield index


def is_escaped_pattern(s):
    for symbol in '*?[{':
        i = s.find(symbol)
        if i > 0:
            if s[i-1] == '\\':
                return True
    return False
