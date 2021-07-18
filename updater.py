from sqlalchemy.orm import session
from db import db_session
from db.models import *
from datetime import date, datetime, timedelta
import os

ALIVE_TIME = timedelta(hours=1)

db_session.global_init()
session = db_session.create_session()

clips = session.query(Clips).all()

for clip in clips:
    print(clip.time_created)
    if datetime.now() - clip.time_created > ALIVE_TIME:
        filename = clip.streamer.name + '_' + str(clip.id)
        try:
            os.remove('static/clips/' + filename + '.mp4')
        except:
            pass
        try:
            os.remove('static/screenshots/' + filename + '.jpg')
        except:
            pass
        clip.streamer.activity -= 1
        session.delete(clip)
session.commit()
