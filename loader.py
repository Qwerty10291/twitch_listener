import streamlink
import subprocess
import twitch
import threading
import os
from datetime import datetime, timedelta
import multiprocessing

class StreamListener:   
    oauth = '0gn793kk3c98a6ugz38tt7zgoq6i0g'
    buffer_lenght = 1024 * 50000
    phraze_handling_timeout = timedelta(seconds=10)

    def __init__(self, streamer) -> None:
        self.streamer = streamer
        self.is_listening = True

    def run(self):
        """начальная инициализация"""
        self.phraze_timer = datetime.now()
        self.phrazes = self.load_phrazes()
        print(self.phrazes)
        self.chat = twitch.Chat('#' + self.streamer, nickname='vamban__', oauth='oauth:' + self.oauth)
        self.session = streamlink.Streamlink()
        self.session.set_option('twitch-oauth-token', self.oauth)

        self.chat.subscribe(self._phrazes_handler)

        self.listener_thread = threading.Thread(target=self._stream_listener)
        self.listener_thread.run()
        self.listener_thread.join()

    def run_in_proccess(self):
        self.process = multiprocessing.Process(target=self.run)
        self.process.start()
        print(self.process.pid)

    def stop(self):
        """остановка процесса"""
        if getattr(self, 'process', None):
            self.process.terminate()
        else:
            self.chat.dispose()
            self.is_listening = False
    
    def save_buffer(self, phraze):
        """обработка и сохранение данных из буфера"""

        if len(self.video) < self.buffer_lenght * 0.9:
            print(f'not enought video')
            return
        filename = f'{self.streamer}_{phraze}_{datetime.now().second}.mp4'
        with open('b_' + filename, 'wb') as file:
            file.write(self.video)
        subprocess.call(['ffmpeg', '-err_detect', 'ignore_err', '-i', f'b_{filename}', '-ss', '00:00:00', '-t', '00:00:40', '-c', 'copy', '-y', filename])
        os.remove('b_' + filename)
        subprocess.call(['ffmpeg', '-ss', '00:00:10', '-i', filename, '-vframes', '1', '-q:v', '2',  filename.replace('.mp4', '.jpg')])

    
    def _phrazes_handler(self, message):
        """обработчик сообщений чата"""
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
        """запись стрима в буфер"""
        self.stream = self.session.streams('https://www.twitch.tv/' + self.streamer)['best'].open()
        print(self.stream)
        self.video = bytearray()
        while True:
            if not self.is_listening:
                break
            self.video += self.stream.read(4096)
            if len(self.video) > self.buffer_lenght:
                del self.video[:len(self.video) - self.buffer_lenght]

    @staticmethod
    def load_phrazes():
        """загрузка фраз из файла"""
        with open('phrazes.txt', 'r', encoding='utf-8') as file:
            return file.read().split('\n')

if __name__ == '__main__':
    nerkin = StreamListener('nerkinlive')
    nerkin.run_in_proccess()
    alcest = StreamListener('alcest_m')
    alcest.run_in_proccess()