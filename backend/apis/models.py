from flask import Flask, session, jsonify, request
import uuid

import datetime

from extensions import db

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