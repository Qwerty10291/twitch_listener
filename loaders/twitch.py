from .loader import StreamListener
import twitch


class TwitchListener(StreamListener):

    def run(self):
        super().run()
        self.session.set_option('twitch-oauth-token', self.oauth)
        self.chat = twitch.Chat(
            '#' + self.platform_id.lower(), nickname='vamban__', oauth='oauth:' + self.oauth)
        self.chat.subscribe(self._handle_messages)

        self._stream_listener(self._get_streams())
    
    def _get_streams(self):
        _, streams = self.session.streams('https://twitch.tv/' + self.name)
        if 'best' not in streams:
            raise RuntimeError('cannot load stream list')
        return streams['best']
    
    def _handle_messages(self, message):
        self._phrazes_handler(message.text)