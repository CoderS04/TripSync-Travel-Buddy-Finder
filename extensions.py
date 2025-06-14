import pymongo
from flask_mail import Mail
from flask_socketio import SocketIO

from dotenv import load_dotenv
import os

load_dotenv()

mail = Mail()

socketio = SocketIO(cors_allowed_origins="*")

print(os.getenv('MONGODB_URI'))
client = pymongo.MongoClient(os.getenv('MONGODB_URI'))
# client = pymongo.MongoClient('mongodb://localhost:27017/')
db = client['tripsync_db']
