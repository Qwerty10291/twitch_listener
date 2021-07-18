import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.orm import Session
import sqlalchemy.ext.declarative as dec
from sqlalchemy.orm import session
from sqlalchemy.orm.session import sessionmaker

SqlAlchemyBase = dec.declarative_base()
__factory = None
engine = None
def global_init():
    global __factory, engine


    conn_str = f'postgresql+psycopg2://twitch:qwerty1029@localhost/twitch'
    print(f"Подключение к базе данных по адресу {conn_str}")
    
    engine = sa.create_engine(conn_str, echo=False, pool_size=20, max_overflow=0)
    __factory = orm.sessionmaker(bind=engine)

    from . import models

    SqlAlchemyBase.metadata.create_all(engine)


def create_session() -> Session:
    global __factory
    return __factory()


def get_sessionmaker():
    conn_str = f'postgresql+psycopg2://twitch:qwerty1029@localhost/twitch'
    print(f"Подключение к базе данных в процессе по адресу {conn_str}")
    
    engine = sa.create_engine(conn_str, echo=False, pool_size=20, max_overflow=0)
    factory = orm.sessionmaker(bind=engine)

    from . import models

    SqlAlchemyBase.metadata.create_all(engine)
    return engine, factory
