from faker import Faker
import random
import uuid
from passlib.hash import pbkdf2_sha256
from datetime import datetime, timedelta, time
from pymongo import MongoClient

fake = Faker()
client = MongoClient("mongodb://localhost:27017")
db = client["tripsync_db"]

travel_styles = ["adventure", "relaxation", "culture", "budget", "luxury"]
interests_list = ["hiking", "art", "food", "wildlife", "photography", "shopping", "nightlife", "cities", "history", "beaches", "adventure-sports", "backpacking"]

def random_interests():
    return random.sample(interests_list, k=random.randint(2, 5))

def create_users(n):
    users = []
    for _ in range(n):
        password = "1234"
        user = {
            "_id": uuid.uuid4().hex,
            "first_name": fake.first_name(),
            "last_name": fake.last_name(),
            "email": fake.email(),
            "password": pbkdf2_sha256.encrypt(password),
            "gender": random.choice(["male", "female", "other"]),
            "country": fake.country(),
            "city": fake.city(),
            "birthdate": datetime.combine(fake.date_of_birth(minimum_age=18, maximum_age=60), datetime.min.time()),
            "image": f"https://randomuser.me/api/portraits/{random.choice(['men', 'women'])}/{random.randint(1, 99)}.jpg"
,
            "travel_style": random.choice(travel_styles),
            "interests": random_interests(),
            "isOnline": False,
            "completedTrips": [],
            "joinedTrips": [],
            "agreed_to_terms": True
        }
        users.append(user)
    db.users.insert_many(users)

def create_trips(n, host_ids):
    trips = []
    for _ in range(n):
        start_date = datetime.combine(fake.date_between(start_date='today', end_date='+60d'), time.min)
        end_date = start_date + timedelta(days=random.randint(3, 10))
        trip = {
            "_id": uuid.uuid4().hex,
            "title": fake.sentence(nb_words=3),
            "destination": fake.country(),
            "specificLocation": fake.city(),
            "startDate": start_date,
            "endDate": end_date,
            "description": fake.text(80),
            "hostID": random.choice(host_ids),
            "image": f"https://source.unsplash.com/800x600/?{random.choice(['beach', 'mountains', 'city', 'forest', 'desert'])},travel"
,
            "travelPreferences": {
                "travelStyle": random.choice(travel_styles),
                "budget": random.choice(["budget", "mid-range", "high-end", "luxury"]),
                "activities": random_interests()
            },
            "companionPreferences": {
                "ageRange": "20-35",
                "groupSize": str(random.randint(2, 8)),
                "communicationStyle": random.sample(["talkative", "quiet", "adventurous", "organized", "spontaneous", "night-owl", "early-riser"], random.randint(2,4)),
                "smokingPreference": random.choice(["non-smoker", "smoker", "no-preference"]),
                "alcoholPreference": random.choice(["non-drinker", "social-drinker", "no-preference"]),
                "genderPreference": random.choice(["male", "female", "no-preference"]),
                "otherRequirements": "no"
            },
            "logistics": {
                "accommodationType": random.choice(["hostel", "budget-hotel", "mid-range-hotel", "luxury-hotel", "airbnb", "camping", "no-preference"]),
                "roomSharing": random.choice(["shared-room", "private-room", "flexible", "no-preference"]),
                "mealPreference": random.choice(["non-vegetarian", "pure-vegetarian", "flexible", "no-preference"])
            },
            "joinedUsers": [],
            "joinRequests": [],
            "createdAt": datetime.now()
        }
        trips.append(trip)
    db.trips.insert_many(trips)

def create_reviews(n, user_ids, trip_ids, host_ids):
    reviews = []
    for _ in range(n):
        review = {
            "_id": uuid.uuid4().hex,
            "tripId": random.choice(trip_ids),
            "hostId": random.choice(host_ids),
            "reviewerId": random.choice(user_ids),
            "rating": round(random.uniform(3.0, 5.0), 1),
            "comment": fake.sentence(),
            "timestamp": datetime.now()
        }
        reviews.append(review)
    db.reviews.insert_many(reviews)

# Run
# create_users(500)
user_ids = [u["_id"] for u in db.users.find({}, {"_id": 1})]
# create_trips(200, host_ids=random.sample(user_ids, 100))
trip_ids = [t["_id"] for t in db.trips.find({}, {"_id": 1})]

create_reviews(400, user_ids, trip_ids, host_ids=user_ids)
