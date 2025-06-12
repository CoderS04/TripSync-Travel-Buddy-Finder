from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd

from extensions import db

def recommend_trips(user_id):
    user = db.users.find_one({"_id": user_id})
    trips = list(db.trips.find())

    if not user or not trips:
        # return jsonify({"error": "User or trips not found"}), 404
        return {"error": "User or trips not found"}

    # Prepare data
    user_vector = {
        "travelStyle": [user.get("travel_style", "").lower()],
        "activities": [interest.lower() for interest in user.get("interests", [])]
    }

    trip_vectors = []
    trip_ids = []

    for trip in trips:
        travel_pref = trip.get("travelPreferences", {})
        trip_vector = {
            "travelStyle": [travel_pref.get("travelStyle", "").lower()],
            "activities": [a.lower() for a in travel_pref.get("activities", [])]
        }
        trip_vectors.append(trip_vector)
        trip_ids.append(str(trip["_id"]))

    # One-hot encode travelStyle and activities
    df_user = pd.DataFrame([user_vector])
    df_trips = pd.DataFrame(trip_vectors)

    mlb_style = MultiLabelBinarizer()
    mlb_acts = MultiLabelBinarizer()

    travel_styles = pd.DataFrame(mlb_style.fit_transform(df_trips["travelStyle"]), columns=mlb_style.classes_)
    activities = pd.DataFrame(mlb_acts.fit_transform(df_trips["activities"]), columns=mlb_acts.classes_)

    df_trips_encoded = pd.concat([travel_styles, activities], axis=1)

    # Encode user in the same format
    user_style = pd.DataFrame(mlb_style.transform(df_user["travelStyle"]), columns=mlb_style.classes_)
    user_acts = pd.DataFrame(mlb_acts.transform(df_user["activities"]), columns=mlb_acts.classes_)
    df_user_encoded = pd.concat([user_style, user_acts], axis=1)

    # Compute similarity
    scores = cosine_similarity(df_user_encoded, df_trips_encoded)[0]
    top_indices = scores.argsort()[::-1][:5]

    # Get recommended trip IDs and scores
    recommended = [{"trip_id": trip_ids[i], "score": round(float(scores[i]), 2)} for i in top_indices]

    # return jsonify(recommended)
    return recommended

def search_trips(data):
    # data = request.json  # from frontend
    destination = data.get("destination")
    travel_style = data.get("travelStyle")
    budget = data.get("budget")
    duration = data.get("duration")

    query = {}
    if destination:
        query["destination"] = destination
    if travel_style:
        query["travelPreferences.travelStyle"] = travel_style
    if budget:
        query["travelPreferences.budget"] = budget

    results = list(db.trips.find(query))

    # Filter duration (in days) manually if needed
    if duration:
        min_days, max_days = map(int, duration.split("-")) if "-" in duration else (int(duration.replace("+", "")), float("inf"))
        results = [r for r in results if min_days <= r['endDate']-r['startDate'] <= max_days]

    return results