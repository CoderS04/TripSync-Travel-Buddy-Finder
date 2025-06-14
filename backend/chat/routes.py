from flask import Flask, Blueprint, session, render_template, redirect, jsonify
from flask_socketio import join_room, emit, leave_room

import datetime

from extensions import db,socketio

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
def open_chat_home():
    if 'logged_in' not in session:
        return redirect('/login')
    return render_template("chatroom.html", user=session['user'])

@chat_bp.route('/trip/<trip_id>')
def open_trip_chat(trip_id):
    if 'logged_in' not in session:
        return redirect('/login')
    
    user_id = session['user']['_id']
    trip = db.trips.find_one({"_id": trip_id})
    if not trip:
        return "Trip not found", 404

    if user_id not in trip.get('joinedUsers', []) and user_id != trip.get('hostID'):
        return "Unauthorized", 403

    return render_template("chatroom.html", user=session['user'])

@chat_bp.route('/private/<buddy_id>')
def open_private_chat(buddy_id):
    if 'logged_in' not in session:
        return redirect('/login')
    return render_template("chatroom.html", user=session['user'])

@chat_bp.route('/<trip_id>')
def group_chat(trip_id):
    # Validate user is part of the trip
    if not 'logged_in' in session:
        return redirect('/login')
    
    user_id = session['user']['_id']
    trip = db.trips.find_one({"_id": trip_id})
    if not trip:
        return "Trip not found", 404

    if user_id not in [u for u in trip.get('joinedUsers', [])] and user_id != trip.get('hostID'):
        return "Unauthorized to access this chat", 403

    return render_template("chatroom.html", trip_id=trip_id, trip_title=trip['title'], user=session['user'])

@chat_bp.route('/history/<room_id>')
def get_chat_history(room_id):
    if room_id.startswith('trip_'):
        trip_id = room_id.replace('trip_', '')
        chats = list(db.chats.find({"tripId": trip_id}))
    else:
        u1, u2 = room_id.split("_")
        chats = list(db.chats.find({
            "type": "private",
            "$or": [
                {"senderId": u1, "receiverId": u2},
                {"senderId": u2, "receiverId": u1}
            ]
        }))

    for chat in chats:
        chat["_id"] = str(chat["_id"])
        if isinstance(chat.get("timestamp"), datetime.datetime):
            chat["timestamp"] = chat["timestamp"].strftime("%Y-%m-%d %H:%M")

        # Lookup sender's name
        user = db.users.find_one({"_id": chat["senderId"]}, {"first_name": 1, "last_name": 1})
        if user:
            chat["senderName"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        else:
            chat["senderName"] = "Unknown User"

    return jsonify(chats)

@socketio.on('join')
def handle_join(data):
    print("joining room")
    room = data['room']
    join_room(room)
    print(f"User joined room: {room}")

@socketio.on('send_message')
def handle_message(data):
    message = {
        "type": data['type'],
        "senderId": session['user']['_id'],
        "message": data['message'],
        "timestamp": datetime.datetime.now()
    }

    user = session['user']
    message["senderName"] = f"{user.get('first_name')} {user.get('last_name')}"

    if data['type'] == 'group':
        message['tripId'] = data['tripId']
    elif data['type'] == 'private':
        message['receiverId'] = data['receiverId']

    db.chats.insert_one(message)
    # Convert timestamp to string for live display
    message["timestamp"] = message["timestamp"].strftime("%Y-%m-%d %H:%M")
    emit('receive_message', message, to=data['room'])

@socketio.on('leave')
def handle_leave(data):
    leave_room(data['room'])
