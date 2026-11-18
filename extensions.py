import pymongo
from flask_mail import Mail
from flask_socketio import SocketIO

from dotenv import load_dotenv
import os

load_dotenv()

mail = Mail()

socketio = SocketIO(cors_allowed_origins="*")

mongo_uri = os.getenv('MONGODB_URI')
if not mongo_uri:
    raise RuntimeError("MONGODB_URI is not configured")

client = pymongo.MongoClient(mongo_uri)
db = client['tripsync_db']
