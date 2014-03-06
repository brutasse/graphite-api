"""Copyright 2008 Orbitz WorldWide

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

     http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License."""

import os.path
import shutil
import tempfile
import time

from flask import request


def is_pattern(s):
    return '*' in s or '?' in s or '[' in s or '{' in s


def write_index(whisper_dir=None, ceres_dir=None, index=None):
    try:
        fd, tmp = tempfile.mkstemp()
        try:
            tmp_index = os.fdopen(fd, 'wt')
            build_index(whisper_dir, ".wsp", tmp_index)
            build_index(ceres_dir, ".ceres-node", tmp_index)
        finally:
            tmp_index.close()
        shutil.move(tmp, index)
    finally:
        try:
            os.unlink(tmp)
        except:
            pass
    return None


def build_index(base_path, extension, fd):
    t = time.time()
    total_entries = 0
    contents = os.walk(base_path, followlinks=True)
    extension_len = len(extension)
    for (dirpath, dirnames, filenames) in contents:
        path = dirpath[len(base_path):].replace('/', '.')
        for metric in filenames:
            if metric.endswith(extension):
                metric = metric[:-extension_len]
            else:
                continue
            line = "{0}.{1}\n".format(path, metric)
            total_entries += 1
            fd.write(line)
    fd.flush()
    print("[IndexSearcher] index rebuild of \"%s\" took %.6f seconds "
          "(%d entries)" % (base_path, time.time() - t, total_entries))
    return None


class RequestParams(object):
    """Dict-like structure that allows accessing request params
    whatever their origin (json body, form body, request args)."""

    def __getitem__(self, key):
        if request.json and key in request.json:
            return request.json[key]
        if key in request.form:
            return request.form[key]
        if key in request.args:
            return request.args[key]
        raise KeyError

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            return False

    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default

    def getlist(self, key):
        if request.json and key in request.json:
            return self[key]
        if key in request.form:
            return request.form.getlist(key)
        return request.args.getlist(key)
RequestParams = RequestParams()
