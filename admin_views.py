from db.db_session import create_session
from db.models import *
from db import logic
from flask_admin.contrib.sqla import ModelView
import os
from loader_controller import StreamerController
from flask import request

class UserView(ModelView):
    can_create = False

    form_columns = ['login', 'password', 'role', 'is_approved']

class GameView(ModelView):
    def delete_model(self, model):
        logic.on_delete_game(model)
        super().delete_model(model)

    form_excluded_columns = ['id', 'streamers']
    form_columns = ['name', 'streamers']

class StreamerView(ModelView):
    def create_model(self, form):
        name = request.form.get('name')
        controller = StreamerController()
        if not controller.check_streamer_exist(name):
            return False
        return super().create_model(form)

    def delete_model(self, model:Streamer):
        logic.on_delete_streamer(model)
        print(model)
        super().delete_model(model)

    form_columns = ['game', 'name']


class TriggerView(ModelView):
    form_excluded_columns = ['id']
    form_columns = ['id', 'name']
