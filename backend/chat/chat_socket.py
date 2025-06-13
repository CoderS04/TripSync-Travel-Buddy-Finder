# chat_socket.py
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import session

socketio = SocketIO(cors_allowed_origins="*")

# In-memory user-room tracking (optional: move to DB)
online_users = {}
room_members = {}

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    user_id = session.get('user_id')
    for room, users in room_members.items():
        if user_id in users:
            users.remove(user_id)
            emit('user-left', {'username': session.get('first_name'), 'users': users}, to=room)

@socketio.on('join-room')
def handle_join(data):
    room = data['room']
    user_id = data['userId']
    username = data['username']
    join_room(room)

    if room not in room_members:
        room_members[room] = set()
    room_members[room].add(user_id)

    emit('user-joined', {'username': username, 'users': list(room_members[room])}, to=room)
    print(f"{username} joined room {room}")

@socketio.on('leave-room')
def handle_leave(data):
    room = data['room']
    user_id = data['userId']
    username = data['username']
    leave_room(room)

    if room in room_members and user_id in room_members[room]:
        room_members[room].remove(user_id)
        emit('user-left', {'username': username, 'users': list(room_members[room])}, to=room)
        print(f"{username} left room {room}")

@socketio.on('send-message')
def handle_send_message(data):
    emit('message', data, to=data['room'])

@socketio.on('private-message')
def handle_private_message(data):
    to_user = data['to']
    emit('private-message', data, to=to_user)  # broadcast to recipient
    emit('private-message', data, to=request.sid)  # echo back to sender

@socketio.on('send-invitation')
def handle_invitation(data):
    to_user = data['to']
    emit('invitation', data, to=to_user)
