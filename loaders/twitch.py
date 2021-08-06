from .loader import StreamListener
import twitch


class TwitchListener(StreamListener):

    def run(self):
        super().run()
        self.session.set_option('twitch-oauth-token', self.oauth)
        self.chat = twitch.Chat(
            '#' + self.platform_id.lower(), nickname='vamban__', oauth='oauth:' + self.oauth)
        self.chat.subscribe(self._handle_messages)

        _, streams = self.session.streams('https://twitch.tv/' + self.name)
        self._stream_listener(streams['best'])
    
    
    def _handle_messages(self, message):
        self._phrazes_handler(message.text)