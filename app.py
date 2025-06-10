from flask import Flask, render_template, session, redirect
from functools import wraps

from extensions import db

app = Flask(__name__)
app.secret_key = b's\x8d\xf2Wh\x90\xdd\x9bQ%\xb2\xa1\x95\xa4\xd1;'

from backend.user.routes import user_bp
app.register_blueprint(user_bp)

from backend.trips.routes import trip_bp
app.register_blueprint(trip_bp)

from backend.apis.routes import api_bp
app.register_blueprint(api_bp)

# Upload configuration
app.config['UPLOAD_FOLDER_TRIPS'] = 'static/uploads/trips/'
app.config['UPLOAD_FOLDER_USERS'] = 'static/uploads/users/'
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB max

def login_required(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            return redirect('/')
    
    return wrap


@app.route('/')
def home():
    return render_template('home.html')

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signup')
def signup():
    return render_template('signup.html')

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

    print(users)

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

if __name__ == '__main__':
    app.run(debug=True)