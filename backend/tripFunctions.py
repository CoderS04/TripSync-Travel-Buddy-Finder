import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MultiLabelBinarizer

from extensions import db

def get_user(user_id):
    return db.users.find_one({"_id": user_id})

def get_all_users():
    return list(db.users.find())

def get_all_trips():
    return list(db.trips.find())

def get_all_ratings():
    return list(db.trip_ratings.find())

# Step 1: Content-Based Scoring
def content_scores(user, trips):
    df = pd.DataFrame(trips)
    df["activities"] = df["travelPreferences"].apply(lambda x: x.get("activities", []))
    df["style"] = df["travelPreferences"].apply(lambda x: x.get("travelStyle", ""))
    df["features"] = df["activities"] + df["style"].apply(lambda x: [x])

    mlb = MultiLabelBinarizer()
    trip_features_matrix = mlb.fit_transform(df["features"])
    
    user_features = user["interests"] + [user["travel_style"]]
    user_vector = mlb.transform([user_features])

    similarity_scores = cosine_similarity(user_vector, trip_features_matrix).flatten()
    content_scores = dict(zip(df["_id"], similarity_scores))

    return content_scores

# Step 2: Collaborative Scoring (User-based)
def collaborative_scores(user_id, all_trips, ratings_data):
    df = pd.DataFrame(ratings_data)
    if df.empty:
        return {}

    rating_matrix = df.pivot_table(index="userId", columns="tripId", values="rating").fillna(0)

    if user_id not in rating_matrix.index:
        return {}

    user_vector = rating_matrix.loc[user_id]
    similarity = cosine_similarity([user_vector], rating_matrix)[0]
    sim_users = pd.Series(similarity, index=rating_matrix.index).drop(user_id)

    score_sums = {}
    sim_sums = {}

    for other_user, sim_score in sim_users.items():
        for trip_id, rating in rating_matrix.loc[other_user].items():
            if rating > 0 and user_vector[trip_id] == 0:
                score_sums[trip_id] = score_sums.get(trip_id, 0) + sim_score * rating
                sim_sums[trip_id] = sim_sums.get(trip_id, 0) + sim_score

    final_scores = {}
    for trip_id in score_sums:
        if sim_sums[trip_id] > 0:
            final_scores[trip_id] = score_sums[trip_id] / sim_sums[trip_id]

    # Normalize to [0, 1]
    max_rating = 5.0
    return {tid: score / max_rating for tid, score in final_scores.items()}

# Step 3: Hybrid Scoring (Combine both)
def hybrid_recommend(user_id, alpha=0.5, top_n=10):
    user = get_user(user_id)
    trips = get_all_trips()
    ratings = get_all_ratings()

    content = content_scores(user, trips)
    collab = collaborative_scores(str(user_id), trips, ratings)

    hybrid = []
    for trip in trips:
        tid = trip["_id"]
        c_score = content.get(tid, 0)
        cf_score = collab.get(tid, 0)
        final = alpha * c_score + (1 - alpha) * cf_score
        hybrid.append((trip, final))

    hybrid.sort(key=lambda x: x[1], reverse=True)
    return hybrid[:top_n]

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

def recommend_buddies(user_id, top_n=10):
    all_users = get_all_users()
    target_user = next((u for u in all_users if u["_id"] == user_id), None)
    if not target_user:
        return []

    df = pd.DataFrame(all_users)
    
    # Combine interests and travel style
    df["features"] = df["interests"].apply(lambda x: x if isinstance(x, list) else []) + df["travel_style"].apply(lambda x: [x])

    mlb = MultiLabelBinarizer()
    feature_matrix = mlb.fit_transform(df["features"])
    
    index = df.index[df["_id"] == user_id][0]
    user_vector = feature_matrix[index].reshape(1, -1)

    similarities = cosine_similarity(user_vector, feature_matrix).flatten()
    df["similarity"] = similarities

    # Filter out self
    recommendations = df[df["_id"] != user_id].sort_values(by="similarity", ascending=False)
    return recommendations.head(top_n).to_dict("records")

from bson.regex import Regex

def search_buddies(data):
    keyword = data.get("keyword", "").strip().lower()
    gender = data.get("gender")
    country = data.get("country", "").strip()
    travel_style = data.get("travelStyle")
    interests = data.get("interests", [])

    # Build Mongo query
    query = {}

    if gender:
        query["gender"] = gender

    if country:
        # Allow partial and case-insensitive match
        query["country"] = Regex(country, "i")

    if travel_style:
        query["travel_style"] = travel_style

    if interests and isinstance(interests, list):
        query["interests"] = {"$in": interests}

    # Run initial MongoDB query
    print("Mongo query:", query)
    users = list(db.users.find(query))

    print(f"Found {len(users)} users matching filters")

    # Now apply keyword search (client-side filter)
    if keyword:
        keyword = keyword.lower()
        def matches_keyword(user):
            name = f"{user.get('first_name', '')} {user.get('last_name', '')}".lower()
            country = user.get("country", "").lower()
            city = user.get("city", "").lower()
            interests = " ".join(user.get("interests", [])).lower()
            return (
                keyword in name or
                keyword in city or
                keyword in country or
                keyword in interests
            )

        users = [user for user in users if matches_keyword(user)]
        print(f"Filtered down to {len(users)} users after keyword match")

    return users
