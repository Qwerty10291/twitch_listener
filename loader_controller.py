from time import time
from typing import List
import twitch
from db import db_session
from db.models import *
from loader import StreamListener
import time
import threading


def singleton(class_):
    instances = {}
    def getinstance(*args, **kwargs):
        if class_ not in instances:
            instances[class_] = class_(*args, **kwargs)
        return instances[class_]
    return getinstance

class StreamerControllerChild:
    def __init__(self, streamer:Streamer, api:twitch.Helix) -> None:
        self.is_streaming = False
        self.streamer = streamer
        self.api = api
        self.listener = StreamListener(streamer)
        
    
    def check_streaming(self):
        session = db_session.create_session()
        session.add(self.streamer)

        user = self.api.user(self.streamer.name)

        if user.is_live:
            print(self.streamer.name, 'online')
            self.streamer.is_online = True
            if not self.is_streaming:
                self.is_streaming = True
                self.listener.run_in_proccess()
        else:
            print(self.streamer.name, 'offline')
            self.streamer.is_online = False
            if self.is_streaming:
                self.is_streaming = False
                self.listener.stop()
        session.commit()
        session.close()


@singleton
class StreamerController:
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    client_id = 'jkomyxxtzay4ze86r16pfh2gmqlmx8'
    client_secret = 'umjmm0oj3kxnznzgjk5ouysc7tf7fl'
    update_time = 10

    def __init__(self) -> None:
        self.api = twitch.Helix(self.client_id, self.client_secret)
        self.streamers = self._load_streamers()
        self.update_thread = self.run_updater()
    
    def run_updater(self):
        update_thread = threading.Thread(target=self._update_timer, daemon=True)
        update_thread.start()
        return update_thread
    
    def check_streamer_exist(self, name):
        user = self.api.user(name)
        return bool(user)
    
    def add_streamer(self, streamer:Streamer):
        controller = StreamerControllerChild(streamer, self.api)
        controller.check_streaming()
        self.streamers.append(controller)
    
    def _update_timer(self):
        while True:
            for streamer in self.streamers:
                streamer.check_streaming()
            time.sleep(self.update_time)

    def _load_streamers(self) -> List[StreamerControllerChild]:
        session = db_session.create_session()
        streamers = session.query(Streamer).all()
        session.expunge_all()
        controllers = [StreamerControllerChild(streamer, self.api) for streamer in streamers]
        for controller in controllers:
            controller.check_streaming()
        return controllers

if __name__ == '__main__':
    db_session.global_init()
    controller = StreamerController()