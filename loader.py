import ffmpeg
import streamlink
from streamlink import session
import subprocess
import twitch
import threading
import os
from datetime import datetime, timedelta

class StreamListener:
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    buffer_lenght = 1024 * 50000
    phraze_handling_timeout = timedelta(seconds=10)

    def __init__(self, streamer) -> None:
        self.phrazes = self.load_phrazes()
        print(self.phrazes)
        self.streamer = streamer
        self.phraze_timer = datetime.now()

        self.chat = twitch.Chat('#' + self.streamer, nickname='vamban__', oauth='oauth:' + self.oauth)
        self.session = streamlink.Streamlink()
        self.session.set_option('twitch-oauth-token', self.oauth)

        self.chat.subscribe(self._phrazes_handler)

        self.listener_thread = threading.Thread(target=self._stream_listener)
        self.listener_thread.run()

    
    def save_buffer(self, phraze):
        if len(self.video) < self.buffer_lenght * 0.9:
            print(f'not enought video')
            return
        filename = f'{self.streamer}_{phraze}_{datetime.now().second}.mp4'
        print(len(self.video))
        with open('b_' + filename, 'wb') as file:
            file.write(self.video)
        subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', f'b_{filename}', '-ss', '00:00:00', '-t', '00:00:40', '-c', 'copy', '-y', filename])
        os.remove('b_' + filename)
        ffmpeg.input(filename).trim(start_frame=0, end_frame=1).output(filename.replace('.mp4', '.png')).run()

    
    def _phrazes_handler(self, message):
        print(message.text)
        if datetime.now() - self.phraze_timer < self.phraze_handling_timeout:
            return
        text = message.text.lower()
        for phraze in self.phrazes:
            if phraze.lower() in text:
                self.phraze_timer = datetime.now()
                print(f'detected in {self.streamer}: {phraze}')
                self.save_buffer(phraze)
                break

    def _stream_listener(self):
        self.stream = self.session.streams('https://www.twitch.tv/' + self.streamer)['best'].open()
        print(self.stream)
        self.video = bytearray()
        while True:
            self.video += self.stream.read(4096)
            if len(self.video) > self.buffer_lenght:
                del self.video[:len(self.video) - self.buffer_lenght]

    @staticmethod
    def load_phrazes():
        with open('phrazes.txt', 'r', encoding='utf-8') as file:
            return file.read().split('\n')

StreamListener('pwgood')