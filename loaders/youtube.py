import threading
from .loader import StreamListener
import pytchat


class YoutubeListener(StreamListener):
    def run(self):
        super().run()
        stream = self._get_streams()
        self.video_id = self.plugin.video_id
        self.chat_thread = threading.Thread(target=self._chat_cycle, daemon=True)
        self.chat_thread.start()
        self.chat_listening = True
        self._stream_listener(stream)
    
    def _get_streams(self):
        plugin, streams = self.session.streams(f'https://youtube.com/channel/{self.platform_id}/live')
        self.plugin = plugin
        if 'best' not in streams:
            raise RuntimeError('cannot load stream list')
        return streams['best']
    
    def stop_listening(self):
        super().stop_listening()
        self.chat_listening = False

    def _chat_cycle(self):
        self.chat = pytchat.create(video_id=self.video_id, interruptable=False)
        while self.chat_listening:
            try:
                if self.chat.is_alive():
                    for c in self.chat.get().sync_items():
                        self._phrazes_handler(c.message)
                else:
                    break
            except:
                self.logger.exception('chat error')
        self.is_listening = False
    