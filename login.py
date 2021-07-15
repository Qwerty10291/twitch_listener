from flask_login import LoginManager
login_manager = LoginManager()
from db import db_session
from db.models import Users
from flask import redirect

@login_manager.user_loader
def load_user(user_id):
    session = db_session.create_session()
    return session.query(Users).get(user_id)

@login_manager.unauthorized_handler
def unathorize():
    return redirect('/login')