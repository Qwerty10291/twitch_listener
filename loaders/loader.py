import logging
from typing import List
from requests.sessions import session
import streamlink
import subprocess
import threading
import os
from datetime import datetime, timedelta
import multiprocessing
from db import db_session
from db.models import *
import time
import logging

class StreamListener:
    oauth = '47sd2dgns59tveokd49kn9dykcocmx'
    buffer_lenght = 1024 * 70000
    recieving_bytes_amount = 8192 * 2
    trigger_timeout = timedelta(minutes=2)
    phrazes_buffer_range = timedelta(seconds=30)
    save_timeout = 20
    listening_after_triggering = timedelta(seconds=15)
    phraze_threshold = 2
    clip_path = './static/clips/'
    screenshot_path = './static/screenshots/'

    def __init__(self, streamer_id) -> None:
        self.streamer_id = streamer_id
        self.is_listening = True
        self.can_deleting_message_buffer = True

    def run(self):
        """начальная инициализация"""

        self.engine, self.session_maker = db_session.get_sessionmaker()

        self._load_streamer()
        self.phrazes = self.load_phrazes()
        self.logger = logging.getLogger('Listener ' + self.name)
        self.logger.info('start')
        self.trigger_timer = datetime.now()

        self.chat_buffer: List[datetime] = []

        self.session = streamlink.Streamlink()
        self.session.set_option('hls-playlist-reload-attempts', 5)
        self.session.set_option('hls-timeout', 15)

    def run_in_proccess(self):
        """запуск слушателя в отдельном процессе"""
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

    def stop(self):
        """остановка процесса"""
        if getattr(self, 'process', None):
            if self.process.is_alive():
                self.process.kill()

    def save_buffer(self, activity):
        """обработка и сохранение данных из буфера"""
        if len(self.video) < self.buffer_lenght * 0.9:
            print(f'not enought video')
            return
        clip = Clips(activity=activity)
        try:
            session = self.session_maker()
            session.add(self.streamer)

            self.streamer.clips.append(clip)
            self.streamer.activity += 1
            streamer = self.streamer
            session.commit()
        except:
            session = self.session_maker()
            streamer = session.query(Streamer).get(self.streamer.id)
            streamer.clips.append(clip)
            streamer.activity += 1
            session.commit()
        self.logger.info('saving buffer with activity: ' + str(activity))

        filename = f'{streamer.name}_{clip.id}.mp4'
        clip_path = self.clip_path + filename
        screen_path = self.screenshot_path + filename.replace('.mp4', '.jpg')
        with open('b_' + filename, 'wb') as file:
            file.write(self.video)
        subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i',
                        f'b_{filename}', '-ss', '00:00:00', '-t', '00:02:00', '-c', 'copy', '-y', clip_path], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.remove('b_' + filename)
        subprocess.call(['ffmpeg', '-ss', '00:00:10', '-i', clip_path,
                        '-vframes', '1', '-q:v', '2',  screen_path],  stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        session.close()
    

    def _phrazes_handler(self, message, time=None):
        """обработчик сообщений чата"""
        if time is None:
            time = datetime.now()
        else:
            if type(time) is str:
                time = datetime.strptime(time, '%Y-%m-%d %H:%M:%S')
        
        self._chat_buffer_update()
        for phraze in self.phrazes:
            if phraze in message:
                self.logger.info('trigger:' + phraze)
                self.chat_buffer.append(time)
                break
        if len(self.chat_buffer) >= self.phraze_threshold and datetime.now() - self.trigger_timer > self.trigger_timeout:
            self.trigger_timer = datetime.now()
            timer_thread = threading.Thread(target=self._save_by_timer, args=(
                self.listening_after_triggering.seconds, ))
            timer_thread.start()

    def _stream_listener(self, stream):
        """запись стрима в буфер"""
        self.stream = stream.open()
        self.video = bytearray()
        self.logger.info('start listening stream')
        while True:
            if not self.is_listening:
                break
            try:
                data = self.stream.read(self.recieving_bytes_amount)
            except Exception as e:
                self.logger.exception('unable to reload playlist')
            try:
                self.video += data
                if len(self.video) > self.buffer_lenght:
                    del self.video[:len(self.video) - self.buffer_lenght]
            except:
                pass
        

    def _save_by_timer(self, seconds):
        """функция для потока таймера запуска"""
        self.logger.info('start count activity ' + str(seconds))
        self.can_deleting_message_buffer = False
        time.sleep(seconds)
        phrazes_count = len(self.chat_buffer)
        self.can_deleting_message_buffer = True
        self.logger.info('starting wait timeout')
        time.sleep(self.save_timeout)
        self.save_buffer(phrazes_count)
        self.chat_buffer.clear()

    def _chat_buffer_update(self):
        """обновление буфера чата"""
        if not self.can_deleting_message_buffer:
            return

        count = 0
        for i in range(len(self.chat_buffer)):
            if datetime.now() - self.chat_buffer[i] > self.phrazes_buffer_range:
                count += 1
            else:
                break
        if count:
            del self.chat_buffer[:count + 1]

    def load_phrazes(self):
        """загрузка фраз из базы данных"""
        session = self.session_maker()
        phrazes = session.query(Trigger).all()
        names = [phraze.name for phraze in phrazes]
        session.close()
        return names
    
    def _load_streamer(self):
        session = self.session_maker()
        self.streamer :Streamer = session.query(Streamer).get(self.streamer_id)
        self.name = self.streamer.name
        self.platform = self.streamer.platform
        self.platform_id = self.streamer.platform_id
        session.close()
        