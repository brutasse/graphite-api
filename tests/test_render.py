import json
import os
import time

import whisper

from . import TestCase, WHISPER_DIR


class RenderTest(TestCase):
    db = os.path.join(WHISPER_DIR, 'test.wsp')

    def test_render_view(self):
        url = '/render'

        response = self.app.get(url, query_string={'target': 'test',
                                                   'format': 'json'})
        self.assertEqual(json.loads(response.data.decode('utf-8')), [])

        response = self.app.get(url, query_string={'target': 'test'})
        self.assertEqual(response.headers['Content-Type'], 'image/png')

        whisper.create(self.db, [(1, 60)])

        ts = int(time.time())
        whisper.update(self.db, 0.5, ts - 2)
        whisper.update(self.db, 0.4, ts - 1)
        whisper.update(self.db, 0.6, ts)

        response = self.app.get(url, query_string={'target': 'test',
                                                   'format': 'json'})
        data = json.loads(response.data.decode('utf-8'))
        end = data[0]['datapoints'][-4:]
        self.assertEqual(
            end, [[None, ts - 3], [0.5, ts - 2], [0.4, ts - 1], [0.6, ts]])

        response = self.app.get(url, query_string={'target': 'test',
                                                   'maxDataPoints': 2,
                                                   'format': 'json'})
        data = json.loads(response.data.decode('utf-8'))
        # 1 is a time race cond
        self.assertTrue(len(data[0]['datapoints']) in [1, 2])

        response = self.app.get(url, query_string={'target': 'test',
                                                   'maxDataPoints': 200,
                                                   'format': 'json'})
        data = json.loads(response.data.decode('utf-8'))
        self.assertEqual(len(data[0]['datapoints']), 60)

    def test_render_validation(self):
        url = '/render'
        whisper.create(self.db, [(1, 60)])

        response = self.app.get(url)
        self.assertJSON(response, {'errors': {
            'target': 'This parameter is required.'}}, status_code=400)

        response = self.app.get(url, query_string={'graphType': 'foo',
                                                   'target': 'test'})
        self.assertJSON(response, {'errors': {
            'graphType': "Invalid graphType 'foo', must be one of 'line', "
            "'pie'."}}, status_code=400)

        response = self.app.get(url, query_string={'maxDataPoints': 'foo',
                                                   'target': 'test'})
        self.assertJSON(response, {'errors': {
            'maxDataPoints': 'Must be an integer.'}}, status_code=400)

        response = self.app.get(url, query_string={
            'from': '21:20_140313',
            'until': '21:20_140313',
            'target': 'test'})
        self.assertJSON(response, {'errors': {
            'from': 'Invalid empty time range',
            'until': 'Invalid empty time range',
        }}, status_code=400)

        response = self.app.get(url, query_string={
            'target': 'foo',
            'width': 100,
            'thickness': '1.5',
            'fontBold': 'true',
            'fontItalic': 'default',
        })
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url, query_string={'target': 'foo',
                                                   'tz': 'Europe/Lausanne'})
        self.assertJSON(response, {'errors': {
            'tz': "Unknown timezone: 'Europe/Lausanne'.",
        }}, status_code=400)

        response = self.app.get(url, query_string={'target': 'test:aa',
                                                   'graphType': 'pie'})
        self.assertJSON(response, {'errors': {
            'target': "Invalid target: 'test:aa'.",
        }}, status_code=400)

        response = self.app.get(url, query_string={'target': ['test',
                                                              'foo:1.2'],
                                                   'graphType': 'pie'})
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url, query_string={'target': ['test', '']})
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url, query_string={'target': 'test',
                                                   'format': 'csv'})
        lines = response.data.decode('utf-8').strip().split('\n')
        self.assertEqual(len(lines), 60)
        self.assertFalse(any([l.strip().split(',')[2] for l in lines]))

        response = self.app.get(url, query_string={'target': 'test',
                                                   'format': 'svg',
                                                   'jsonp': 'foo'})
        jsonpsvg = response.data.decode('utf-8')
        self.assertTrue(jsonpsvg.startswith('foo("<?xml version=\\"1.0\\"'))
        self.assertTrue(jsonpsvg.endswith('</script>\\n</svg>")'))

        response = self.app.get(url, query_string={'target': 'test',
                                                   'format': 'svg'})
        svg = response.data.decode('utf-8')
        self.assertTrue(svg.startswith('<?xml version="1.0"'))

        response = self.app.get(url, query_string={
            'target': 'sum(test)',
        })
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url, query_string={
            'target': ['sinFunction("a test", 2)',
                       'sinFunction("other test", 2.1)',
                       'sinFunction("other test", 2e1)'],
        })
        self.assertEqual(response.status_code, 200)

        response = self.app.get(url, query_string={
            'target': ['percentileOfSeries(sin("foo bar"), 95, true)']
        })
        self.assertEqual(response.status_code, 200)

    def test_raw_data(self):
        url = '/render'
        whisper.create(self.db, [(1, 60)])

        response = self.app.get(url, query_string={'rawData': '1',
                                                   'target': 'test'})
        info, data = response.data.decode('utf-8').strip().split('|', 1)
        path, start, stop, step = info.split(',')
        datapoints = data.split(',')
        self.assertEqual(datapoints, ['None'] * 60)
        self.assertEqual(int(stop) - int(start), 60)
        self.assertEqual(path, 'test')
        self.assertEqual(int(step), 1)

    def test_jsonp(self):
        url = '/render'
        whisper.create(self.db, [(1, 60)])

        start = int(time.time()) - 59
        response = self.app.get(url, query_string={'format': 'json',
                                                   'jsonp': 'foo',
                                                   'target': 'test'})
        data = response.data.decode('utf-8')
        self.assertTrue(data.startswith('foo('))
        data = json.loads(data[4:-1])
        try:
            self.assertEqual(data, [{'datapoints': [
                [None, start + i] for i in range(60)
            ], 'target': 'test'}])
        except AssertionError:  # Race condition when time overlaps a second
            self.assertEqual(data, [{'datapoints': [
                [None, start + i + 1] for i in range(60)
            ], 'target': 'test'}])
