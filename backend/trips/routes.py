from flask import Flask, Blueprint, session, redirect, render_template, jsonify
from backend.trips.models import Trip
from backend.apis.models import API

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
    trip = Trip().getTripById(trip_id)
    if not trip:
        return "Trip not found", 404
    
    host = Trip().getUserById(trip["hostID"])

    ratingData = API().getRatingSummary(trip["hostID"])

    return render_template(
        'tripDetails.html',
        trip = trip,
        host = host,
        averageRating = round(ratingData["averageRating"], 1),
        ratingCount=ratingData["ratingCount"])

@trip_bp.route("/<trip_id>/join_request", methods=["POST"])
def request_to_join_trip(trip_id):
    if 'logged_in' in session:
        return Trip().joinTripRequest(trip_id)
    else:
        return jsonify({"error": "You are not logged in"}), 401

@trip_bp.route("/<trip_id>/requests")
def view_join_requests(trip_id):
    if 'logged_in' in session:
        trip = Trip().getTripById(trip_id)
        if session['user']['_id'] != trip["hostID"]:
            return "Unauthorized", 403

        for req in trip['joinRequests']:
            u = Trip().getUserById(req['userId'])
            req['user'] = u

        return render_template("reviewRequests.html", trip=trip)
    else:
        return redirect('/')

@trip_bp.route("/<trip_id>/approve/<user_id>", methods=["POST"])
def approve_join_request(trip_id, user_id):
    if 'logged_in' in session:
        trip = Trip().getTripById(trip_id)

        if session['user']['_id'] != trip["hostID"]:
            return "Unauthorized", 403

        Trip().approveRequest(trip_id, user_id)

        return redirect(f"/trip/{trip_id}/requests")
    else:
        return redirect('/')

@trip_bp.route("/<trip_id>/reject/<user_id>", methods=["POST"])
def reject_join_request(trip_id, user_id):
    if 'logged_in' in session:
        trip = Trip().getTripById(trip_id)

        if session['user']['_id'] != trip["hostID"]:
            return "Unauthorized", 403

        Trip().rejectRequest(trip_id, user_id)

        return redirect(f"/trip/{trip_id}/requests")
    else:
        return redirect('/')
    
@trip_bp.route("/<trip_id>/companions")
def tripCompanions(trip_id):
    if 'logged_in' in session:
        trip = Trip().getTripById(trip_id)
        if session['user']['_id'] != trip["hostID"]:
            return "Unauthorized", 403
        
        companions=[]
        for user in trip['joinedUsers']:
            companions.append(Trip().getUserById(user))

        return render_template('tripCompanions.html', trip = trip, companions=companions)