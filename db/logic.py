from sqlalchemy.orm.session import Session
from .models import *
from .db_session import create_session

def init_session(func):
    def wrapper(*argv, **kwargs):
        if 'session' not in kwargs:
            session = create_session()
        else:
            session = kwargs.pop('session')
        func(*argv, session=session, **kwargs)
        session.close()
    return wrapper

@init_session
def create_user(login, password, is_admin=False, session:Session=None):
    if session.query(Users).filter(Users.login == login):
        return False
    
    user = Users(login=login, password=password)
    if is_admin:
        user.role = 'admin'
    session.add(user)
    session.commit()
    session.close()
