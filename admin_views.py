from db.db_session import create_session
from db.models import *
from db import logic
from flask_admin.contrib.sqla import ModelView
import os
from loader_controller import StreamerController
from flask import request, flash

class UserView(ModelView):
    can_create = False
    def delete_model(self, model):
        if model.role == 'admin':
            return flash('нельзя удалить администратора')
        else:
            return super().delete_model(model)

    form_columns = ['login', 'password', 'role', 'is_approved']

class GameView(ModelView):
    def delete_model(self, model):
        logic.on_delete_game(model)
        return super().delete_model(model)

    form_excluded_columns = ['id', 'streamers']
    form_columns = ['name', 'streamers']

class StreamerView(ModelView):

    def create_model(self, form):
        name = request.form.get('name')
        controller = StreamerController()
        if not controller.check_streamer_exist(name):
            return False
        streamer = super().create_model(form)
        self.session.expunge(streamer)
        controller.add_streamer(streamer)
        return True
    
    def delete_model(self, model):
        self.on_model_delete(model)
        logic.on_delete_streamer(model)
        StreamerController().delete_streamer(model)
        self.session.delete(model)
        self.session.commit()
        self.after_model_delete(model)
    

    form_columns = ['game', 'name']


class TriggerView(ModelView):
    form_excluded_columns = ['id']
    form_columns = ['id', 'name']
