from flask import *
from flask import request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from flask_marshmallow import Marshmallow 
import os
from werkzeug.security import generate_password_hash, check_password_hash
from passlib.hash import sha256_crypt

myapp = Flask(__name__)
myapp.secret_key = "VERY_SECRET_KEY"

basedir = os.path.abspath(os.path.dirname(__file__))
myapp.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db.sqlite')
myapp.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# print(myapp.config)

db = SQLAlchemy(myapp)
ma = Marshmallow(myapp)
is_authenticated = False

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True, autoincrement=True)
    name = db.Column(db.String(50))
    username = db.Column(db.String(30), unique = True)
    password = db.Column(db.String(128))

    def __init__(self, name, username):
        self.name = name
        self.username = username
    
    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'name', 'username', 'password')

user_schema = UserSchema()
users_schema = UserSchema(many=True)

@myapp.route('/')
def index():
    if is_authenticated:
        return redirect(url_for('home'))
    else:
        return render_template('index.html')

@myapp.route('/register', methods = ['GET'])
def get_register():
    if is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect('/')

@myapp.route('/register', methods = ['POST'])
def post_register():
    name = request.form['name']
    uname = request.form['uname']
    pswd1 = request.form['pswd1']
    pswd2 = request.form['pswd2']
    new_user = User(name = name, username = uname)

    usr = False
    engine = create_engine("sqlite:///db.sqlite")
    
    if engine.dialect.has_table(engine, 'user'):
        usr = User.query.filter_by(username = uname).first()
    else:
        usr = False

    valid = 1
    error = []

    if usr:
        error.append("User already exists!")
        return render_template('index.html', error = error)
    else:
        if len(pswd1) != len(pswd2) and pswd1 != pswd2:
            error.append('Both passwords must match')
            valid = 0
        if len(pswd1) < 8:
            error.append('Password must be 8 letters')
            valid = 0
        
        if valid == 0:
            return render_template('index.html', error = error)
        else:
            new_user.set_password(pswd1)
            db.session.add(new_user)
            db.session.commit()
            global is_authenticated
            is_authenticated = True
            session['username'] = uname
            return redirect(url_for('home'))            

@myapp.route('/login', methods = ['GET'])
def get_login():
    if is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('index'))

@myapp.route('/login', methods = ['POST'])
def login():
    username = request.form['uname']
    password = request.form['pswd']
    error = []
    usr = User.query.filter_by(username = username).first()
    if usr:
        auth = usr.check_password(password)
        if auth:
            global is_authenticated
            is_authenticated = True
            session['username'] = username
            return redirect(url_for('home'))
        else:
            error.append("Invalid Credentials")
    else:
        error.append("Credentials don't match with database")

    return render_template('index.html', error = error)
    # return redirect('/home')

@myapp.route('/logout')
def logout():
    session.clear()
    global is_authenticated
    is_authenticated = False
    return redirect('/') 

@myapp.route('/home')
def home():
    return render_template('home.html')

if __name__ == "__main__":
    myapp.run(host = "0.0.0.0", port = "7000")