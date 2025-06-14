from flask import Flask, Blueprint, session, render_template, redirect, jsonify
from flask_socketio import join_room, emit

import datetime

from extensions import db,socketio

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

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
    # For group: room_id = trip_<tripId>
    # For private: room_id = user1_user2 (sorted)

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
    return jsonify(chats)

@socketio.on('join')
def handle_join(data):
    print("joining room")
    room = data['room']
    join_room(room)
    print(f"User joined room: {room}")

@socketio.on('send_message')
def handle_message(data):
    print('send_message')
    message = {
        "type": data['type'],
        "senderId": session['user']['_id'],
        "message": data['message'],
        "timestamp": datetime.datetime.now()
    }

    if data['type'] == 'group':
        message['tripId'] = data['tripId']
    elif data['type'] == 'private':
        message['receiverId'] = data['receiverId']

    db.chats.insert_one(message)
    emit('receive_message', message, to=data['room'])

