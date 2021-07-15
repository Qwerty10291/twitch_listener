from typing import List
from sqlalchemy.sql.sqltypes import DateTime
import streamlink
import subprocess
import twitch
import threading
import os
from datetime import datetime, timedelta
import multiprocessing
from db import db_session
from db.models import *
import time


class StreamListener:
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    buffer_lenght = 1024 * 50000
    recieving_bytes_amount = 8192 * 2
    trigger_timeout = timedelta(minutes=1)
    phrazes_buffer_range = timedelta(seconds=60)
    listening_after_triggering = timedelta(seconds=15)
    phraze_threshold = 1

    def __init__(self, streamer: Streamer) -> None:
        self.streamer = streamer
        self.is_listening = True
        self.can_deleting_message_buffer = True

    def run(self):
        """начальная инициализация"""
        print('starting', self.streamer.name)
        db_session.global_init()

        self.phrazes = self.load_phrazes()
        self.trigger_timer = datetime.now()

        self.chat = twitch.Chat(
            '#' + self.streamer.name, nickname='vamban__', oauth='oauth:' + self.oauth)
        self.chat_buffer: List[DateTime] = []

        self.session = streamlink.Streamlink()
        self.session.set_option('twitch-oauth-token', self.oauth)

        self.chat.subscribe(self._phrazes_handler)

        self.listener_thread = threading.Thread(target=self._stream_listener)
        self.listener_thread.run()
        self.listener_thread.join()

    def run_in_proccess(self):
        """запуск слушателя в отдельном процессе"""
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()

    def stop(self):
        """остановка процесса"""
        print('stopping', self.streamer.name)
        if getattr(self, 'process', None):
            self.process.terminate()
        else:
            self.chat.dispose()
            self.is_listening = False

    def save_buffer(self, activity):
        """обработка и сохранение данных из буфера"""
        if len(self.video) < self.buffer_lenght * 0.9:
            print(f'not enought video')
            return
        
        print('starting', activity)
        session = db_session.create_session()
        session.add(self.streamer)
        clip = Clips(activity=activity)
        self.streamer.clips.append(clip)
        self.streamer.activity += 1
        session.commit()
        

        filename = f'{clip.id}.mp4'
        file_path = os.path.join(os.os.getcwd(), '/static/clips', filename)
        with open('b_' + filename, 'wb') as file:
            file.write(self.video)
        subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i',
                        f'b_{filename}', '-ss', '00:00:00', '-t', '00:00:40', '-c', 'copy', '-y', file_path])
        os.remove('b_' + filename)
        subprocess.call(['ffmpeg', '-ss', '00:00:10', '-i', file_path,
                        '-vframes', '1', '-q:v', '2',  file_path.replace('.mp4', '.jpg')])
        session.close()

    def _phrazes_handler(self, message):
        """обработчик сообщений чата"""
        text = message.text.lower()
        self._chat_buffer_update()
        for phraze in self.phrazes:
            if phraze in text:
                self.chat_buffer.append(datetime.now())
                break
        if len(self.chat_buffer) >= self.phraze_threshold and datetime.now() - self.trigger_timer > self.trigger_timeout:
            self.trigger_timer = datetime.now()
            timer_thread = threading.Thread(target=self._save_by_timer, args=(self.listening_after_triggering.seconds, ))
            timer_thread.start()

    def _stream_listener(self):
        """запись стрима в буфер"""
        self.stream = self.session.streams(
            'https://www.twitch.tv/' + self.streamer.name)['best'].open()
        self.video = bytearray()
        print('started listening stream')
        while True:
            if not self.is_listening:
                break
            self.video += self.stream.read(self.recieving_bytes_amount)
            if len(self.video) > self.buffer_lenght:
                del self.video[:len(self.video) - self.buffer_lenght]

    def _save_by_timer(self, seconds):
        """функция для потока таймера запуска"""
        self.can_deleting_message_buffer = False
        time.sleep(seconds)
        phrazes_count = len(self.chat_buffer)
        self.save_buffer(phrazes_count)
        self.can_deleting_message_buffer = True
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

    @staticmethod
    def load_phrazes():
        """загрузка фраз из базы данных"""
        session = db_session.create_session()
        phrazes = session.query(Trigger).all()
        return [phraze.name for phraze in phrazes]
    