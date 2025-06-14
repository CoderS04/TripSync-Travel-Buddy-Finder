import pymongo
from flask_mail import Mail
from flask_socketio import SocketIO

mail = Mail()

socketio = SocketIO(cors_allowed_origins="*")

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['tripsync_db']
