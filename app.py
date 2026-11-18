from flask import Flask, render_template, session, redirect
from functools import wraps

from dotenv import load_dotenv
import os

from extensions import db, mail, socketio

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is not configured")

from backend.user.routes import user_bp
app.register_blueprint(user_bp)

from backend.trips.routes import trip_bp
app.register_blueprint(trip_bp)

from backend.apis.routes import api_bp
app.register_blueprint(api_bp)

from backend.chat.routes import chat_bp
app.register_blueprint(chat_bp)

socketio.init_app(app)
from flask_cors import CORS
CORS(app)

# Upload configuration
app.config['UPLOAD_FOLDER_TRIPS'] = 'static/uploads/trips/'
app.config['UPLOAD_FOLDER_USERS'] = 'static/uploads/users/'
app.config['UPLOAD_FOLDER_IDPROOFS'] = 'static/uploads/idProof/'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

# Mail config
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('GMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('GMAIL_PASSWORD')  # Use App Password from Gmail
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('GMAIL_USER')
mail.init_app(app)

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/login')
    
    return wrap


@app.route('/')
def home():
    if 'logged_in' in session:
        return redirect('/dashboard')
    
    return render_template('home.html')

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/login')
def login():
    if not 'logged_in' in session:
        return render_template('login.html')
    
    return redirect('/dashboard')

@app.route('/signup')
def signup():
    if not 'logged_in' in session:
        return render_template('signup.html')
    
    return redirect('/dashboard')

@app.route('/dashboard')
@login_required
def dashboard():
    hostedTrips = list(db["trips"].find({ "hostID": session['user']['_id'] }))
    joinedTrips = list(db["trips"].find({ "joinedUsers": session['user']['_id'] }))
    users = {}
    for trip in joinedTrips:
        for userId in trip["joinedUsers"]:
            user = db.users.find_one({'_id':userId})

            user_image = user.get('image', '')

            users[userId] = user_image

    return render_template("dashboard.html", hostedTrips=hostedTrips, joinedTrips= joinedTrips, joinedUsers = users)

@app.route('/find-trips')
def findTrips():
    return render_template('findTrips.html')

@app.route('/host')
@login_required
def host():
    return render_template('hostTrip.html')

@app.route('/find-buddy')
def findBuddy():
    return render_template('findBuddy.html')

@app.route('/<userId>')
@login_required
def userProfile(userId):
    user = db.users.find_one({'_id': userId})
    if user:
        return render_template('profile.html', user = user)
    else:
        return redirect('/')

@app.before_request
def set_user_session():
    if 'user' in session:
        session['user_id'] = session['user']['_id']
        session['first_name'] = session['user']['first_name']

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=int(os.getenv('PORT', '5000')), debug=os.getenv('FLASK_DEBUG', '0') == '1')