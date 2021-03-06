from time import time
from typing import List
import streamlink
import twitch
from db import db_session
from db.models import *
from loaders.twitch import TwitchListener
from loaders.youtube import YoutubeListener
import time
import threading
import logging
import requests

from twitch_api import TwitchApi

def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


class StreamerControllerChild:
    def __init__(self, streamer: Streamer, api: TwitchApi) -> None:
        self.is_streaming = False
        self.streamer = streamer
        session = db_session.create_session()
        session.add(self.streamer)
        self.name = self.streamer.name
        self.platform_id = self.streamer.platform_id
        self.platform = self.streamer.platform
        self.streamer_id = self.streamer.id
        session.close()
        self.listener = self.get_listener()
        self.logger = logging.getLogger(f'Child {self.name}')
        self.api = api
        self.check_streaming()

    def check_streaming(self):
        session = db_session.create_session()
        try:
            session.add(self.streamer)
        except:
            session = session.object_session(self.streamer)

        try:
            status = self.check_alive()
            if status is None:
                status = False
        except Exception as e:
            self.logger.exception('unknown error')
            time.sleep(30)

        if status:
            self.streamer.is_online = True
            session.commit()
            session.close()
            if not self.is_streaming:
                self.start()
            else:
                try:
                    if not self.listener.process.is_alive():
                        self.logger.error('process dead but streamer is streaming now. reopen')
                        self.listener = self.get_listener()
                        self.start()
                except Exception as msg:
                    self.logger.exception('failed to reopen process')
        else:
            try:
                self.streamer.is_online = False
                session.commit()
                session.close()
                if self.is_streaming:
                    self.stop()
            except Exception as e:
                self.logger.exception('unknown error when stop listener')

    def get_listener(self):
        if self.platform == 'twitch':
            return TwitchListener(self.streamer_id)
        elif self.platform == 'youtube':
            return YoutubeListener(self.streamer_id)

    def on_delete(self):
        if self.is_streaming:
            self.logger.info('delete')
            self.listener.stop()
    
    def start(self):
        self.logger.info('run')
        self.is_streaming = True
        self.listener.run_in_proccess()
    
    def stop(self):
        self.logger.info('stop')
        self.is_streaming = False
        try:
            self.listener.stop()
        except:
            self.logger.exception('failed to stop listener')

    def check_alive(self):
        if self.platform == 'twitch':
            try:
                return self.api.check_live(self.platform_id)
            except Exception as e:
                self.logger.exception('twitch api error')
                return False
        elif self.platform == 'youtube':
            try:
                streams = streamlink.Streamlink().streams(
                    f'https://youtube.com/channel/{self.platform_id}/live')
                return bool(streams[1])
            except Exception as e:
                self.logger.exception('youtube check failed')
                return False


@singleton
class StreamerController:
    oauth = 'bc7upb6rmi8o3rc4zg0d5uaxztntg4'
    client_id = 'jkomyxxtzay4ze86r16pfh2gmqlmx8'
    client_secret = 'umjmm0oj3kxnznzgjk5ouysc7tf7fl'
    youtube_key = 'AIzaSyDBvLYQ9kcjeJ3NMD5gWav3nmNzQoH7AOs'
    update_time = 10

    def __init__(self) -> None:
        self.logger = logging.getLogger('Parent')
        self.twitch_client = TwitchApi(self.client_id, self.oauth)
        self.streamers = self._load_streamers()
        self.update_thread = self.run_updater()

    def run_updater(self):
        update_thread = threading.Thread(
            target=self._update_timer, daemon=True)
        update_thread.start()
        return update_thread

    def check_streamer_exist(self, platform, platform_id) -> str:
        if platform == 'twitch':
            try:
                user = self.twitch_client.get_user(platform_id)
                return user.display_name
            except NameError:
                return None
            except ValueError:
                self.logger.exception('unknown twitch api error')
                raise ApiError()
        elif platform == 'youtube':
            try:
                data = requests.get('https://www.googleapis.com/youtube/v3/channels',
                                    params={'key': self.youtube_key, 'id': platform_id, 'part': 'brandingSettings'}).json()
                if data['pageInfo']['totalResults']:
                    return data['items'][0]['brandingSettings']['channel']['title']
                else:
                    return None
            except:
                raise ApiError()

    def add_streamer(self, streamer: Streamer):
        controller = StreamerControllerChild(streamer, self.twitch_client)
        self.streamers.append(controller)

    def delete_streamer(self, streamer):
        for i in range(len(self.streamers)):
            if streamer.name == self.streamers[i].name:
                self.streamers[i].on_delete()
                del self.streamers[i]
                break
    
    def close_all(self):
        for controller in self.streamers:
            controller.stop()

    def _update_timer(self):
        while True:
            for streamer in self.streamers:
                streamer.check_streaming()
            time.sleep(self.update_time)

    def _load_streamers(self) -> List[StreamerControllerChild]:
        self.logger.info('Init controller')
        session = db_session.create_session()
        streamers = session.query(Streamer).all()
        session.close()
        controllers = [StreamerControllerChild(
            streamer, self.twitch_client) for streamer in streamers]
        for controller in controllers:
            controller.check_streaming()
        return controllers


if __name__ == '__main__':
    db_session.global_init()
    controller = StreamerController()


class ApiError(Exception):
    pass
