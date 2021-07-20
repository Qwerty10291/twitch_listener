from flask_restful import Resource, reqparse
from flask import jsonify, abort
from db import db_session
from db.models import *
from loader_controller import ApiError, StreamerController
from flask_login import login_required, current_user

game_parser = reqparse.RequestParser()
game_parser.add_argument('name', required=True, type=str, location='form')

def admin_required(func):
    def wrapper(*args, **kwargs):
        if current_user.role != 'admin':
            return jsonify({'error': 'вы не администратор'})
        return func(*args, **kwargs)
    return wrapper

def provide_session(func):
    def wrapper(*args, **kwargs):
        session = db_session.create_session()
        try:
            result = func(*args, session=session, **kwargs)
            session.close()
            return result
        except:
            print('db api error in', func.__name__)
            return abort(500)
    return wrapper

class GameResource(Resource):
    @login_required
    @provide_session
    def get(self, session=None):
        games = session.query(Game).all()
        return jsonify([game.to_dict(only=('id', 'name', 'streamers.id', 'streamers.name', 'streamers.activity', 'streamers.is_online')) for game in games])

    @login_required
    @admin_required
    @provide_session
    def post(self, session=None):
        args = game_parser.parse_args()
        game = session.query(Game).filter(Game.name == args.name).one_or_none()
        if game:
            return jsonify({'error': 'игра с таким названием уже существует'})
        game = Game(name=args.name)
        session.add(game)
        session.commit()
        return jsonify(game.to_dict(only=('id', 'name')))
    



streamer_parser = reqparse.RequestParser()
streamer_parser.add_argument('name', required=True, type=str, location='form')
streamer_parser.add_argument('game', required=True, type=str, location='form')


class StreamerResource(Resource):
    @login_required
    @provide_session
    def get(self, id, session=None):
        session = db_session.create_session()
        streamer = session.query(Streamer).get(id)
        if not streamer:
            return jsonify({'error': 'стримера с таким id нет'})
        
        json = streamer.to_dict(only=('id', 'game_id', 'name', 'activity', 'is_online', 'clips.id', 'clips.activity', 'clips.time_created'))
        for clip in json['clips']:
            clip['image'] = f'static/screenshots/{streamer.name}_{clip["id"]}.jpg'
            clip['video'] = f'static/clips/{streamer.name}_{clip["id"]}.mp4'
        return jsonify(json)

    @login_required
    @admin_required
    @provide_session
    def delete(self, id, session=None):
        session = db_session.create_session()
        streamer = session.query(Streamer).get(id)
        if not streamer:
            return jsonify({'error': 'стримера с таким id нет'})
        StreamerController().delete_streamer(streamer)
        session.delete(streamer)
        session.commit()
        return jsonify({'success': 'OK'})
    
class StreamerListResource(Resource):
    @login_required
    @provide_session
    def get(self, session=None):
        streamers = session.query(Streamer).order_by(Streamer.activity.desc()).all()

        return jsonify([streamer.to_dict(only=('id', 'name', 'activity', 'is_online', 'game.id', 'game.name')) for streamer in streamers])
    
    @login_required
    @admin_required
    @provide_session
    def post(self, session=None):
        args = streamer_parser.parse_args()
        if 'twitch.tv' in args.name:
            args.name = args.name.split('/')[-1]
        game = session.query(Game).filter(Game.name == args.game).one_or_none()
        if not game:
            game = Game(name=args.game)
            session.add(game)

        streamer = session.query(Streamer).filter(Streamer.name == args.name).one_or_none()
        if streamer:
            return jsonify({'error': 'стример с таким именем уже существует'})

        controller = StreamerController()
        try:
            if not controller.check_streamer_exist(args.name):
                return jsonify({'error': f'стример с именем {args.name} не найден'})
        except ApiError:
            return jsonify({'error': 'ошибка в api твича при проверке пользователя. Повторите попытку.'})
        
        streamer = Streamer(name=args.name)
        game.streamers.append(streamer)
        session.commit()
        
        json = streamer.to_dict(only=('id', 'name', 'is_online', 'game.id', 'game.name'))
        session.expunge_all()
        controller.add_streamer(streamer)
        return jsonify(json)
    
phraze_parser = reqparse.RequestParser()
phraze_parser.add_argument('text', required=True, type=str, location='body')

class PhrazeListResource(Resource):
    @login_required
    @provide_session
    def get(self, session=None):
        phrazes = session.query(Trigger).all()

        return jsonify([phraze.to_dict(only=('id', 'name')) for phraze in phrazes])
    
    @login_required
    @admin_required
    @provide_session
    def post(self, session=None):
        args = phraze_parser.parse_args()   
        trigger = Trigger(name=args.text)
        session.add(trigger)
        session.commit()
        return jsonify(trigger.to_dict())

class PhrazeResource(Resource):
    @login_required
    @provide_session
    def get(self, id, session=None):

        phraze = session.query(Trigger).get(id)
        if not phraze:
            return jsonify({'error': 'фразы с таким id не существует'})
        
        return jsonify(phraze.to_dict(only=('id', 'name')))
    
    @login_required
    @admin_required
    @provide_session
    def delete(self, id, session=None):

        phraze = session.query(Trigger).get(id)
        if not phraze:
            return jsonify({'error': 'фразы с таким id не существует'})
        
        session.delete(phraze)
        session.commit()
        return jsonify({'success': 'OK'})

class UserListResource(Resource):
    @login_required
    @provide_session
    def get(self, session=None):
        users = session.query(Users).all()
        return jsonify([user.to_dict(only=('id', 'login', 'role')) for user in users])