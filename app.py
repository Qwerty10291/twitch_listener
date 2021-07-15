from flask import Flask, render_template, request, redirect, sessions
from db import db_session
from db import logic
from db.models import Users
from loader_controller import StreamerController
from flask_restful import Api
from streamer_resource import GameResource, StreamerResource, StreamerListResource, PhrazeResource, PhrazeListResource
from login import login_manager
from flask_login import login_required, login_user, logout_user, current_user
from forms import LoginForm, RegisterForm
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = b'iwiuwjeiuweulie49812389u298'
login_manager.init_app(app)

api = Api(app)
api.add_resource(GameResource, '/api/game')
api.add_resource(StreamerListResource, '/api/streamer')
api.add_resource(StreamerResource, '/api/streamer/<int:id>')
api.add_resource(PhrazeListResource, '/api/trigger')
api.add_resource(PhrazeResource, '/api/trigger/<int:id>')


@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()

    if form.validate_on_submit():
        session = db_session.create_session()
        login = request.form.get('login')
        user = session.query(Users).filter(Users.login == login).one_or_none()
        if not user:
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        if not check_password_hash(user.password, request.form.get('password')):
            return render_template('login.html', title='Вход', form=form, errors='Неправильный логин или пароль.')

        if not user.is_approved:
            return render_template('login.html', title='Вход', form=form, errors='Администратор не подтвердил заявку на регистрацию')

        login_user(user)
        return redirect('/')
    return render_template('login.html', title='Вход', form=form)

@app.route('/register', methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect('/')

    form = RegisterForm()
    if form.validate_on_submit():
        session = db_session.create_session()
        login = request.form.get('login')
        user = session.query(Users).filter(Users.login == login).one_or_none()

        if user:
            return render_template('register.html', title='Регистрация', form=form, errors="Данный логин занят.")
        hashed_password = generate_password_hash(request.form.get('password'))

        user = Users(login=login, password=hashed_password, role=user, is_approved=True)
        session.add(user)
        session.commit()
        return redirect('/login')
    return render_template('register.html', title='Регистрация', form=form)

@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect('/login')

if __name__ == '__main__':
    db_session.global_init()
    controller = StreamerController()
    app.run('localhost', 8000)