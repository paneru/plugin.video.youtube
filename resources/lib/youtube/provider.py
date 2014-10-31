from functools import partial
from resources.lib import kodimon
from resources.lib.kodimon import DirectoryItem
from resources.lib.kodimon.helper.function_cache import FunctionCache
from resources.lib.youtube import youtube_v3
import youtube_tv

__author__ = 'bromix'


class Provider(kodimon.AbstractProvider):
    def __init__(self, plugin=None):
        kodimon.AbstractProvider.__init__(self, plugin)

        from resources.lib import youtube

        # TODO: set language of XBMC/KODI (en-US) in the client. YouTube will already localize some strings
        settings = self.get_settings()
        self._client = youtube.Client(items_per_page=settings.get_items_per_page())
        pass

    def get_client(self):
        """
        Return the internal client. Respect the class definition!
        :return:
        """
        return self._client

    @kodimon.RegisterPath('^\/channel\/(?P<channel_id>.+)\/playlists/$')
    def _on_channel_playlists(self, path, params, re_match):
        result = []

        channel_id = re_match.group('channel_id')
        page_token = params.get('page_token', '')

        json_data = self._client.get_playlists_v3(channel_id=channel_id, page_token=page_token)
        result.extend(youtube_v3.process_response(self, path, params, json_data))

        return result

    @kodimon.RegisterPath('^\/channel\/(?P<channel_id>.+)\/$')
    def _on_channel(self, path, params, re_match):
        self._set_default_content_type_and_sort_methods()

        result = []

        channel_id = re_match.group('channel_id')
        page = int(params.get('page', 1))
        if page == 1:
            playlists_item = DirectoryItem(self.localize('youtube.playlists'),
                                           self.create_uri(['channel', channel_id, 'playlists']))
            playlists_item.set_fanart(self.get_fanart())
            result.append(playlists_item)
            pass

        # first we must get the id of the upload playlist (thank you Google!)
        json_data = self.call_function_cached(partial(self._client.get_channels_v3, channel_id=channel_id),
                                              seconds=FunctionCache.ONE_DAY)
        items = json_data['items']  # let it crash if not conform
        item = items[0]
        uploads_playlist_id = item.get('contentDetails', {}).get('relatedPlaylists', {}).get('uploads', '')
        if uploads_playlist_id:
            json_data = self._client.get_playlist_items_v3(playlist_id=uploads_playlist_id)
            result.extend(youtube_v3.process_response(self, path, params, json_data))
            pass

        return result

    @kodimon.RegisterPath('^/playlist/(?P<playlist_id>.+)/$')
    def _on_playlist(self, path, params, re_match):
        self._set_default_content_type_and_sort_methods()

        result = []

        playlist_id = re_match.group('playlist_id')
        page_token = params.get('page_token', '')

        json_data = self._client.get_playlist_items_v3(playlist_id=playlist_id, page_token=page_token)
        result.extend(youtube_v3.process_response(self, path, params, json_data))

        return result

    @kodimon.RegisterPath('^/play/$')
    def _on_play(self, path, params, re_match):
        video_id = params['video_id']

        vq = self.get_settings().get_video_quality()

        from . import VideoInfoExtractor
        vie = VideoInfoExtractor(self._client)
        video_stream = vie.get_best_fitting_video_stream(video_id, vq)

        item = kodimon.VideoItem(video_id, video_stream['url'])
        return item

    @kodimon.RegisterPath('^/guide/$')
    def _on_guide(self, path, params, re_match):
        result = []

        # cashing
        json_data = self.call_function_cached(partial(self._client.get_guide_tv), seconds=FunctionCache.ONE_DAY)
        result.extend(youtube_tv.process_response(self, json_data))

        return result

    def on_search(self, search_text, path, params, re_match):
        self._set_default_content_type_and_sort_methods()

        result = []

        page_token = params.get('page_token', '')
        json_data = self._client.search_v3(q=search_text, page_token=page_token)
        result.extend(youtube_v3.process_response(self, path, params, json_data=json_data))

        return result

    def on_root(self, path, params, re_match):
        result = []

        # TODO: call settings dialog for login
        # possible sign in
        #sign_in_item = DirectoryItem('[B]Sign in (Dummy)[/B]', '')
        #result.append(sign_in_item)

        # search
        search_item = DirectoryItem(self.localize(self.LOCAL_SEARCH),
                                    self.create_uri([self.PATH_SEARCH, 'list']))
        search_item.set_fanart(self.get_fanart())
        result.append(search_item)

        # TODO: try to implement 'What to Watch'
        # what to watch
        what_to_watch_item = DirectoryItem('What to watch (Dummy)',
                                           self.create_uri(['browse/tv', self._client.BROWSE_ID_WHAT_TO_WATCH]))
        result.append(what_to_watch_item)

        # TODO: setting to disable this item
        # guide - we call this function the get the localized string directly from YouTube
        json_data = self.call_function_cached(partial(self._client.get_guide_tv), seconds=FunctionCache.ONE_MINUTE * 10)
        if json_data.get('kind', '') == 'youtubei#guideResponse':
            title = json_data.get('items', [{}])[0].get('guideSectionRenderer', {}).get('title', '')
            if title:
                guide_item = DirectoryItem(title,
                                           self.create_uri(['guide']))
                guide_item.set_fanart(self.get_fanart())
                result.append(guide_item)
                pass
            pass

        return result

    def _set_default_content_type_and_sort_methods(self):
        self.set_content_type(kodimon.constants.CONTENT_TYPE_EPISODES)
        self.add_sort_method(kodimon.constants.SORT_METHOD_UNSORTED,
                             kodimon.constants.SORT_METHOD_VIDEO_TITLE,
                             kodimon.constants.SORT_METHOD_VIDEO_YEAR,
                             kodimon.constants.SORT_METHOD_VIDEO_RUNTIME)

    def get_fanart(self):
        """
            This will return a darker and (with blur) fanart
            :return:
            """
        return self.create_resource_path('media', 'fanart.jpg')

    pass