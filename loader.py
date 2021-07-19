from typing import List
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
import sys

class StreamListener:
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    buffer_lenght = 1024 * 50000
    recieving_bytes_amount = 8192 * 2
    trigger_timeout = timedelta(minutes=2)
    phrazes_buffer_range = timedelta(seconds=30)
    save_timeout = 5
    listening_after_triggering = timedelta(seconds=15)
    phraze_threshold = 2
    clip_path = './static/clips/'
    screenshot_path = './static/screenshots/'

    def __init__(self, streamer: Streamer) -> None:
        self.streamer = streamer
        self.is_listening = True
        self.can_deleting_message_buffer = True

    def run(self):
        """начальная инициализация"""
        print('starting', self.streamer.name)
        self.engine, self.session_maker = db_session.get_sessionmaker()

        self.phrazes = self.load_phrazes()
        self.name = self.streamer.name
        self.phraze_threshold = self.streamer.threshold
        self.trigger_timer = datetime.now()

        self.chat = twitch.Chat(
            '#' + self.name.lower(), nickname='vamban__', oauth='oauth:' + self.oauth)
        self.chat_buffer: List[datetime] = []

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
        if getattr(self, 'process', None):
            print('stopping process')
            self.process.kill()
        else:
            self.chat.dispose()
            self.is_listening = False

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
        print('starting', streamer.name, activity)

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

    def _phrazes_handler(self, message):
        """обработчик сообщений чата"""
        text = message.text.lower()
        self._chat_buffer_update()
        for phraze in self.phrazes:
            if phraze in text:
                print(self.name, phraze, len(self.chat_buffer))
                self.chat_buffer.append(datetime.now())
                break
        if len(self.chat_buffer) >= self.phraze_threshold and datetime.now() - self.trigger_timer > self.trigger_timeout:
            self.trigger_timer = datetime.now()
            timer_thread = threading.Thread(target=self._save_by_timer, args=(
                self.listening_after_triggering.seconds, ))
            timer_thread.start()

    def _stream_listener(self):
        """запись стрима в буфер"""
        self.stream = self.session.streams(
            'https://www.twitch.tv/' + self.streamer.name)['best'].open()
        self.video = bytearray()
        print('started listening stream', os.getpid())
        while True:
            if not self.is_listening:
                break
            try:
                data = self.stream.read(self.recieving_bytes_amount)
            except:
                sys.exit()
            try:
                self.video += data
                if len(self.video) > self.buffer_lenght:
                    del self.video[:len(self.video) - self.buffer_lenght]
            except:
                pass

    def _save_by_timer(self, seconds):
        """функция для потока таймера запуска"""
        print('starting count messages', seconds)
        self.can_deleting_message_buffer = False
        time.sleep(seconds)
        phrazes_count = len(self.chat_buffer)
        self.can_deleting_message_buffer = True
        print('starting wait timeout')
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
