from flask import Flask, Blueprint, request, render_template, session, jsonify
from backend.user.models import User
import datetime

from extensions import db

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/signup', methods = ['POST'])
def signup():
    return User().signup()

@user_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        print("trying to verify otp")
        input_otp = request.form.get("otp")
        return User().verifyOTP(input_otp)

    print("trying to render template verify-otp.html")
    return render_template("verify-otp.html")

@user_bp.route('/login', methods = ['POST'])
def login():
    return User().login()

@user_bp.route('/signout')
def signout():
    return User().signout()

# Add this new route to your Flask app file (app.py)

@user_bp.route('/connections/send_request', methods=['POST'])
def send_connection_request():

    if 'user' not in session:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    data = request.get_json()
    recipient_id_str = data.get('recipient_id')

    if not recipient_id_str:
        return jsonify({"success": False, "error": "Recipient ID is required"}), 400

    try:
        sender_id = session['user']['_id']
        recipient_id = recipient_id_str
        
        # Prevent user from sending a request to themselves
        if sender_id == recipient_id:
            return jsonify({"success": False, "error": "You cannot connect with yourself."}), 400

        # Check if they are already connected
        is_connected = db.users.find_one({
            "_id": sender_id,
            "connections.userId": recipient_id
        })
        if is_connected:
            return jsonify({"success": False, "error": "You are already connected."}), 409 # 409 Conflict

        # Check if a request has already been sent to this user
        request_exists = db.users.find_one({
            "_id": recipient_id,
            "connectionRequests": sender_id
        })
        if request_exists:
            return jsonify({"success": False, "error": "Request already sent."}), 409

        # Add the sender's ID to the recipient's connectionRequests array
        # Using $addToSet prevents duplicate requests
        db.users.update_one(
            {"_id": recipient_id},
            {"$addToSet": {"connectionRequests": sender_id}}
        )

        return jsonify({"success": True, "message": "Connection request sent successfully."})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@user_bp.route('/connection_requests')
def get_connection_requests():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session['user']['_id']
        current_user = db.users.find_one({"_id": user_id})

        if not current_user or 'connectionRequests' not in current_user:
            return jsonify([])

        # 'connectionRequests' should be a list of user IDs who sent the request
        request_user_ids = current_user.get('connectionRequests', [])
        
        # Fetch full user details for each request
        requesters = list(db.users.find(
            {"_id": {"$in": request_user_ids}},
            {"first_name": 1, "last_name": 1, "image": 1} # Projection
        ))

        # Convert ObjectId to string for JSON serialization
        for user in requesters:
            user['_id'] = str(user['_id'])

        return jsonify(requesters)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/connections')
def get_connections():

    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        user_id = session['user']['_id']
        current_user = db.users.find_one({"_id": user_id})

        if not current_user or 'connections' not in current_user:
            return jsonify([])

        # Assuming 'connections' is a list of objects: [{'userId': ObjectId, 'date': ISODate}, ...]
        connection_data = current_user.get('connections', [])
        connection_user_ids = [conn['userId'] for conn in connection_data]

        # Fetch full user details for each connection
        connected_users = list(db.users.find(
            {"_id": {"$in": connection_user_ids}},
            {"first_name": 1, "last_name": 1, "image": 1}
        ))
        
        # Create a map for easy lookup
        users_map = {str(user['_id']): user for user in connected_users}

        # Combine user details with connection date
        response_data = []
        for conn in connection_data:
            user_info = users_map.get(str(conn['userId']))
            if user_info:
                response_data.append({
                    "user": {
                        "_id": str(user_info['_id']),
                        "first_name": user_info.get('first_name'),
                        "last_name": user_info.get('last_name'),
                        "image": user_info.get('image')
                    },
                    "date": conn['date'].strftime('%b %d, %Y') # Format date nicely
                })
        
        return jsonify(response_data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/connections/respond', methods=['POST'])
def respond_to_connection_request():

    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()
    requester_id_str = data.get('requester_id')
    action = data.get('action') # 'accept' or 'reject'

    if not requester_id_str or action not in ['accept', 'reject']:
        return jsonify({"error": "Missing or invalid parameters"}), 400

    try:
        current_user_id = session['user']['_id']
        requester_id = requester_id_str
        connection_date = datetime.datetime.now()

        # 1. Remove request from current user's list
        db.users.update_one(
            {"_id": current_user_id},
            {"$pull": {"connectionRequests": requester_id}}
        )

        if action == 'accept':
            # 2. Add connection for both users
            # For current user
            db.users.update_one(
                {"_id": current_user_id},
                {"$addToSet": {"connections": {"userId": requester_id, "date": connection_date}}}
            )
            # For the requester
            db.users.update_one(
                {"_id": requester_id},
                {"$addToSet": {"connections": {"userId": current_user_id, "date": connection_date}}}
            )
        
        return jsonify({"success": True, "message": f"Request {action}ed successfully."})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@user_bp.route('/trips')
def get_user_trips():
    if 'logged_in' not in session:
        return jsonify([])
    user_id = session['user']['_id']
    trips = list(db.trips.find({
        "$or": [
            {"joinedUsers": user_id},
            {"hostID": user_id}
        ]
    }, {"_id": 1, "title": 1}))
    for t in trips:
        t['_id'] = str(t['_id'])
    return jsonify(trips)

@user_bp.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    return User().updateProfile(data)

@user_bp.route('/update-about', methods=['POST'])
def update_about():
    if 'user' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    return User().updateBio(data)
