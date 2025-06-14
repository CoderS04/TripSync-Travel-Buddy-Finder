from flask import Flask, session, jsonify, request
import uuid
import math


import datetime

from extensions import db
from backend.tripFunctions import recommend_buddies, search_buddies

class API():

    def submitReview(self):

        data = request.form
        review = {
            "_id": uuid.uuid4().hex,
            "tripId": data["tripId"],
            "hostId": data["hostId"],
            "reviewerId": session["user"]['_id'],
            "rating": float(data["rating"]),
            "comment": data["comment"],
            "timestamp": datetime.datetime.now()
        }

        db.reviews.insert_one(review)
        return jsonify({"success": "Review submitted!"}), 200
    
    def getRatingSummary(self, id):
        pipeline = [
            {"$match": {"hostId": id}},
            {
                "$group": {
                    "_id": "$hostId",
                    "averageRating": {"$avg": "$rating"},
                    "ratingCount": {"$sum": 1}
                }
            }
        ]

        result = list(db.reviews.aggregate(pipeline))
        return result[0] if result else {"averageRating": 0, "ratingCount": 0}
    
    def recommendBuddies(self):
        userId = session['user']['_id']
        recommended = recommend_buddies(userId)
        results = []

        for user in recommended:
            ratingData = self.getRatingSummary(user['_id'])
            averageRating = round(ratingData["averageRating"], 1),
            ratingCount=ratingData["ratingCount"]
            user['avgRating'] = averageRating
            user['ratingCount'] = ratingCount
            results.append(user)
        
        def clean_data_for_json(data):
            if isinstance(data, dict):
                return {key: clean_data_for_json(value) for key, value in data.items()}
            elif isinstance(data, list):
                return [clean_data_for_json(item) for item in data]
            elif isinstance(data, float) and (math.isnan(data) or math.isinf(data)):
                return None
            elif data == '' or data is None:
                return None
            else:
                return data

        # Before returning JSON:
        cleaned_buddies = clean_data_for_json(results)
        return jsonify(cleaned_buddies)
        # return jsonify(results)
    
    def searchBuddies(self):
        data = request.json
        search = search_buddies(data)

        results = []

        for user in search:
            ratingData = self.getRatingSummary(user['_id'])
            averageRating = round(ratingData["averageRating"], 1),
            ratingCount=ratingData["ratingCount"]
            user['avgRating'] = averageRating
            user['ratingCount'] = ratingCount
            results.append(user)
        
        return jsonify(results)

