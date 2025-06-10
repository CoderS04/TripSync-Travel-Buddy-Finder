from flask import Flask, Blueprint, session, redirect
from backend.trips.models import Trip

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/recommend_trips', methods = ['POST', 'GET'])
def recommend_trips():
    if 'logged_in' in session:
        return Trip().findTrip()
    else:
        return redirect('/')
    
@api_bp.route('/search_trips', methods=['POST', 'GET'])
def search_trips():
    return Trip().searchTrips()
