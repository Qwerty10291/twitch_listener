from flask_restful import Resource, reqparse
from flask import jsonify
from db import db_session
from db.models import *
from loader_controller import StreamerController

game_parser = reqparse.RequestParser()
game_parser.add_argument('name', required=True, type=str, location='form')


class GameResource(Resource):
    def get(self):
        session = db_session.create_session()
        games = session.query(Game).all()
        return jsonify([game.to_dict(only=('id', 'name', 'streamers.id', 'streamers.name', 'streamers.activity', 'streamers.is_online')) for game in games])

    def post(self):
        args = game_parser.parse_args()
        session = db_session.create_session()
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
    def get(self, id):
        session = db_session.create_session()
        streamer = session.query(Streamer).get(id)
        if not streamer:
            return jsonify({'error': 'стримера с таким id нет'})
        
        json = streamer.to_dict(only=('id', 'game_id', 'name', 'activity', 'is_online', 'clips.id', 'clips.activity'))
        for clip in json['clips']:
            clip['image'] = f'static/screenshots/{clip["id"]}.jpg'
            clip['video'] = f'static/clips/{clip["id"]}.mp4'
        return jsonify(json)

    def delete(self, id):
        session = db_session.create_session()
        streamer = session.query(Streamer).get(id)
        if not streamer:
            return jsonify({'error': 'стримера с таким id нет'})
        
        session.delete(streamer)
        session.commit()
        return jsonify({'success': 'OK'})
    
class StreamerListResource(Resource):
    def get(self):
        session = db_session.create_session()
        streamers = session.query(Streamer).order_by(Streamer.activity.desc()).all()

        return jsonify([streamer.to_dict(only=('id', 'name', 'activity', 'is_online', 'game.id', 'game.name')) for streamer in streamers])
    
    def post(self):
        args = streamer_parser.parse_args()
        if 'twitch.tv' in args.name:
            args.name = args.name.split('/')[-1]
        session = db_session.create_session()
        game = session.query(Game).filter(Game.name == args.game).one_or_none()
        if not game:
            game = Game(name=args.game)

        streamer = session.query(Streamer).filter(Streamer.name == args.name).one_or_none()
        if streamer:
            return jsonify({'error': 'стример с таким именем уже существует'})

        controller = StreamerController()
        if not controller.check_streamer_exist(args.name):
            return jsonify({'error': f'стример с именем {args.name} не найден'})
        

        streamer = Streamer(name=args.name)
        game.streamers.append(streamer)
        session.commit()
        
        json = streamer.to_dict(only=('id', 'name', 'is_online', 'game.id', 'game.name'))
        session.expunge(streamer)
        session.expunge(game)
        controller.add_streamer(streamer)

        return jsonify(json)
    
phraze_parser = reqparse.RequestParser()
phraze_parser.add_argument('text', required=True, type=str, location='body')

class PhrazeListResource(Resource):
    def get(self):
        session = db_session.create_session()
        phrazes = session.query(Trigger).all()

        return jsonify([phraze.to_dict(only=('id', 'name')) for phraze in phrazes])
    
    def post(self):
        args = phraze_parser.parse_args()
        session = db_session.create_session()   
        trigger = Trigger(name=args.text)
        session.add(trigger)
        session.commit()
        return jsonify(trigger.to_dict())

class PhrazeResource(Resource):
    def get(self, id):
        session = db_session.create_session()

        phraze = session.query(Trigger).get(id)
        if not phraze:
            return jsonify({'error': 'фразы с таким id не существует'})
        
        return jsonify(phraze.to_dict(only=('id', 'name')))
    
    def delete(self, id):
        session = db_session.create_session()

        phraze = session.query(Trigger).get(id)
        if not phraze:
            return jsonify({'error': 'фразы с таким id не существует'})
        
        session.delete(phraze)
        session.commit()
        return jsonify({'success': 'OK'})