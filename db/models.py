import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy import orm
from datetime import datetime
from sqlalchemy_serializer import SerializerMixin
from flask_login import UserMixin


class Users(SqlAlchemyBase, SerializerMixin, UserMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    login = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    role = sqlalchemy.Column(sqlalchemy.String, default='user')
    is_approved = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    is_online = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    last_online = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())

class UsersQueue(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users_queue'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    user_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('users.id'))
    user = orm.relation('Users')

class Game(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'games'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)
    streamers = orm.relation('Streamer', back_populates='game')

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return self.name

class Streamer(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'streamers'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    game_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('games.id'))
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    activity = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    is_online = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
    game = orm.relation('Game')
    clips = orm.relation('Clips', back_populates='streamer')

    def __str__(self) -> str:
        return self.name
    
    def __repr__(self) -> str:
        return self.name

class Trigger(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'triggers'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    name = sqlalchemy.Column(sqlalchemy.String)

class Clips(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'clips'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    streamer_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey('streamers.id'))
    activity = sqlalchemy.Column(sqlalchemy.Integer)
    time_created = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.now())
    streamer = orm.relation('Streamer')