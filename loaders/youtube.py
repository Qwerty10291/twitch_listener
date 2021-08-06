import threading
from .loader import StreamListener
import pytchat


class YoutubeListener(StreamListener):
    def run(self):
        super().run()
        plugin, streams = self.session.streams(f'https://youtube.com/channel/{self.platform_id}/live')
        self.video_id = plugin.video_id
        self.chat_thread = threading.Thread(target=self._chat_cycle, daemon=True)
        self.chat_thread.start()
        self._stream_listener(streams['best'])

    
    def _chat_cycle(self):
        self.chat = pytchat.create(video_id=self.video_id, interruptable=False)
        while self.chat.is_alive():
            for c in self.chat.get().sync_items():
                self._phrazes_handler(c.message, time=c.datetime)
        self.is_listening = False
    