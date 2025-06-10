import pymongo
from flask_mail import Mail

mail = Mail()

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client['tripsync_db']