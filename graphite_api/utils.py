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
import calendar
import pytz

from flask import request


def is_pattern(s):
    return '*' in s or '?' in s or '[' in s or '{' in s


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
            value = self[key]
            if not isinstance(value, list):
                value = [value]
            return value
        if key in request.form:
            return request.form.getlist(key)
        return request.args.getlist(key)
RequestParams = RequestParams()


def to_seconds(delta):
    return abs(delta.seconds + delta.days * 86400)


def epoch(dt):
    """
    Returns the epoch timestamp of a timezone-aware datetime object.
    """
    return calendar.timegm(dt.astimezone(pytz.utc).timetuple())
