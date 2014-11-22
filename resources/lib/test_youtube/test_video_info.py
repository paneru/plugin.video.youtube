from resources.lib._old_youtube import VideoInfo, Client

__author__ = 'bromix'

import unittest

class TestVideoStreamExtractor(unittest.TestCase):
    def setUp(self):
        self._client = Client()
        pass

    def test_get_best_fitting_video_stream(self):
        vie = VideoInfo(self._client)

        # free
        stream = vie.get_best_fitting_video_stream('Y0noFhiUh1U', 576)
        stream = vie.get_best_fitting_video_stream('Y0noFhiUh1U', 720)
        pass

    def test_video_with_signature(self):
        vie = VideoInfo(self._client)

        # vevo
        streams_tv = vie._method_get_video_info('O-zpOMYRi0w')
        streams_web = vie._get_stream_infos_web('O-zpOMYRi0w')
        pass

    def test_video_without_signature(self):
        vie = VideoInfo(self._client)

        # free
        streams_tv = vie._method_get_video_info('Y0noFhiUh1U')
        streams_web = vie._get_stream_infos_web('Y0noFhiUh1U')
        pass

    pass
