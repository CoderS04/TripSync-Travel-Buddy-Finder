from flask import Flask, Blueprint, session, redirect, render_template, jsonify
from backend.trips.models import Trip

trip_bp = Blueprint('trip', __name__, url_prefix='/trip')

@trip_bp.route('/host', methods = ['POST','GET'])
def host():
    if 'logged_in' in session:
        return Trip().hostTrip()
    else:
        return redirect('/')


@trip_bp.route('/find', methods = ['POST'])
def find():
    if 'logged_in' in session:
        return Trip().findTrip()
    else:
        return redirect('/')
    
@trip_bp.route('/<trip_id>')
def tripDetails(trip_id):
    print(trip_id)
    trip = Trip().getTripById(trip_id)
    if not trip:
        return "Trip not found", 404
    
    host = Trip().getUserById(trip["hostID"])

    return render_template('tripDetails.html', trip = trip, host = host)

@trip_bp.route('/<trip_id>/join', methods=['POST'])
def joinTrip(trip_id):
    print("Joining", trip_id)

    if 'logged_in' in session:
        return Trip().joinTrip(trip_id, session['user']['_id'])

    else:
        return jsonify({"error": "You are not logged in"}), 401
