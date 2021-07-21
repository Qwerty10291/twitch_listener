from time import time
from typing import List
import twitch
from db import db_session
from db.models import *
from loader import StreamListener
import time
import threading
import logging



def singleton(class_):
    instances = {}

    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance


class StreamerControllerChild:
    def __init__(self, streamer: Streamer, api: twitch.Helix) -> None:
        self.is_streaming = False
        self.streamer = streamer
        session = db_session.create_session()
        session.add(self.streamer)
        self.name = self.streamer.name
        session.close()
        self.logger = logging.getLogger(f'Child {self.name}')
        self.api = api
        self.listener = StreamListener(streamer)
        self.check_streaming()

    def check_streaming(self):
        session = db_session.create_session()
        try:
            session.add(self.streamer)
        except:
            session = session.object_session(self.streamer)
        try:
            user = self.api.user(self.name)
            status = user.is_live
        except Exception as e:
            self.logger.exception('twitch api error')
            return

        if status:
            self.streamer.is_online = True
            session.commit()
            session.close()
            if not self.is_streaming:
                self.logger.info('run')
                self.is_streaming = True
                self.listener.run_in_proccess()
        else:
            self.streamer.is_online = False
            session.commit()
            session.close()
            if self.is_streaming:
                self.logger.info('stop')
                self.is_streaming = False
                try:
                    self.listener.stop()
                except:
                    self.logger.exception('failed to stop listener')
    

    def on_delete(self):
        if self.is_streaming:
            self.logger.info('delete')
            self.listener.stop()


@singleton
class StreamerController:
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    client_id = 'jkomyxxtzay4ze86r16pfh2gmqlmx8'
    client_secret = 'umjmm0oj3kxnznzgjk5ouysc7tf7fl'
    update_time = 10

    def __init__(self) -> None:
        self.logger = logging.getLogger('Parent')
        self.api = twitch.Helix(self.client_id, self.client_secret)
        self.streamers = self._load_streamers()
        self.update_thread = self.run_updater()
        

    def run_updater(self):
        update_thread = threading.Thread(
            target=self._update_timer, daemon=True)
        update_thread.start()
        return update_thread

    def check_streamer_exist(self, name):
        try:
            user = self.api.user(name)
        except:
            self.logger.error('twitch api error')
            raise ApiError()
        return bool(user)

    def add_streamer(self, streamer: Streamer):
        controller = StreamerControllerChild(streamer, self.api)
        self.streamers.append(controller)

    def delete_streamer(self, streamer):
        for i in range(len(self.streamers)):
            if streamer.name == self.streamers[i].name:
                self.streamers[i].on_delete()
                del self.streamers[i]
                break

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
            streamer, self.api) for streamer in streamers]
        for controller in controllers:
            controller.check_streaming()
        return controllers


if __name__ == '__main__':
    db_session.global_init()
    controller = StreamerController()


class ApiError(Exception):
    pass
