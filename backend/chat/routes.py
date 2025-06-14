from flask import Flask, Blueprint, session, render_template, redirect, jsonify
from flask_socketio import join_room, emit, leave_room
import uuid
import datetime

from extensions import db, socketio

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
def open_chat_home():
    if 'logged_in' not in session:
        return redirect('/login')
    return render_template("chatroom.html", user=session['user'], chat = {"room" : 'null'})

@chat_bp.route('/trip/<trip_id>')
def open_trip_chat(trip_id):
    if 'logged_in' not in session:
        return redirect('/login')

    user_id = session['user']['_id']  # already a string now
    trip = db.trips.find_one({"_id": trip_id})  # ✅ CHANGED: assume _id is string

    if not trip:
        return "Trip not found", 404

    if user_id not in trip.get('joinedUsers', []) and user_id != trip.get('hostID'):
        return "Unauthorized", 403

    return render_template("chatroom.html", user=session['user'], chat = {"room": f"trip_{trip_id}", "title": trip['title'], "subtitle":"Trip Group Chat"})

@chat_bp.route('/private/<buddy_id>')
def open_private_chat(buddy_id):
    if 'logged_in' not in session:
        return redirect('/login')
    
    connections = [c['userId'] for c in session['user']['connections']]
    if buddy_id not in connections:
        return "Unauthorized", 403

    buddy = db.users.find_one({'_id': buddy_id}, {"first_name": 1, "last_name": 1})

    return render_template("chatroom.html", user=session['user'], chat = {"room": f"{session['user']['_id']}_{buddy_id}", "title": f"{buddy['first_name']} {buddy['last_name']}", "subtitle":"Travel Buddy"})

@chat_bp.route('/<trip_id>')
def group_chat(trip_id):
    if not 'logged_in' in session:
        return redirect('/login')

    user_id = session['user']['_id']
    trip = db.trips.find_one({"_id": trip_id})  # ✅ CHANGED: trip_id is string

    if not trip:
        return "Trip not found", 404

    if user_id not in trip.get('joinedUsers', []) and user_id != trip.get('hostID'):
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
        if isinstance(chat.get("timestamp"), datetime.datetime):
            chat["timestamp"] = chat["timestamp"].strftime("%Y-%m-%d %H:%M")

        # ✅ CHANGED: senderId is now a string, so we query by string
        user = db.users.find_one({"_id": chat["senderId"]}, {"first_name": 1, "last_name": 1})
        if user:
            chat["senderName"] = f"{user.get('first_name', '')} {user.get('last_name', '')}"
        else:
            chat["senderName"] = "Unknown User"

    return jsonify(chats)

@socketio.on('join')
def handle_join(data):
    room = data['room']
    join_room(room)

@socketio.on('send_message')
def handle_message(data):
    sender_id = session['user']['_id']  # ✅ CHANGED: already a string

    message = {
        "_id": uuid.uuid4().hex,  # ✅ CHANGED: use UUID string for message ID
        "type": data['type'],
        "senderId": sender_id,  # ✅ CHANGED: ensure string
        "message": data['message'],
        "timestamp": datetime.datetime.now()
    }

    user = session['user']
    message["senderName"] = f"{user.get('first_name')} {user.get('last_name')}"

    if data['type'] == 'group':
        message['tripId'] = data['tripId']
    elif data['type'] == 'private':
        message['receiverId'] = data['receiverId']  # ✅ CHANGED: already string

    db.chats.insert_one(message)

    # ✅ CHANGED: convert timestamp for emitting
    message["timestamp"] = message["timestamp"].strftime("%Y-%m-%d %H:%M")

    emit('receive_message', message, to=data['room'])

@socketio.on('leave')
def handle_leave(data):
    leave_room(data['room'])
