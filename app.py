from flask import Flask, render_template
from sqlalchemy.orm import session
from db import db_session, models
from db import logic as db

app = Flask(__name__)
app.secret_key = b'iwiuwjeiuweulie49812389u298'

@app.route('/')
def index():
    return 'Hello'

if __name__ == '__main__':
    app.run('localhost', 8000)