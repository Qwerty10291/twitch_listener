from flask import Flask
from db import db_session
from loader_controller import StreamerController
from flask_restful import Api
from streamer_resource import GameResource, StreamerResource, StreamerListResource, PhrazeResource, PhrazeListResource

app = Flask(__name__)
app.secret_key = b'iwiuwjeiuweulie49812389u298'

api = Api(app)
api.add_resource(GameResource, '/api/game')
api.add_resource(StreamerListResource, '/api/streamer')
api.add_resource(StreamerResource, '/api/streamer/<int:id>')
api.add_resource(PhrazeListResource, '/api/trigger')
api.add_resource(PhrazeResource, '/api/trigger/<int:id>')

@app.route('/')
def index():
    return 'Hello'

if __name__ == '__main__':
    db_session.global_init()
    controller = StreamerController()
    app.run('localhost', 8000)