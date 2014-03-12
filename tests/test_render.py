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
        self.assertEqual(len(data[0]['datapoints']), 2)
