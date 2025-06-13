from pymongo import MongoClient
import random

# Connect to your MongoDB
client = MongoClient("mongodb://localhost:27017/")  # Update with your URI if hosted
db = client["tripsync_db"]
collection = db["trips"]

# List of tags
tags = ['beach', 'mountains', 'city', 'forest', 'desert']

import uuid  # or use time for randomness

for trip in collection.find():
    tag = random.randint(1,7)

    image_url = f"/static/uploads/trips/img{tag}.jpg"

    collection.update_one(
        {"_id": trip["_id"]},
        {"$set": {"image": image_url}}
    )

print("All trip images updated.")
