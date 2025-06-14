from flask import Flask, jsonify, request, session, current_app
import uuid
from datetime import datetime

from werkzeug.utils import secure_filename
import os

from backend.tripFunctions import hybrid_recommend,search_trips,recommend_buddies,search_buddies
from backend.apis.models import API

from extensions import db

class Trip:

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def hostTrip(self):
        trips = db["trips"]

        title = request.form.get('trip-title')
        destination = request.form.get('destination')
        specificLocation = request.form.get('specific-location')
        startDate = request.form.get('start-date')
        endDate = request.form.get('end-date')
        description = request.form.get('trip-description')
        userId = session['user']['_id']

        #Travel Preferences
        travelStyle = request.form.get('travel-style')
        budget = request.form.get('budget-range')
        activities = request.form.getlist('activities')
        pace = request.form.get('pace')

        #Companion Preferences
        ageRange = request.form.get('age-range')
        groupSize = request.form.get('group-size')
        communicationStyle = request.form.getlist('communication')
        genderPreference = request.form.get('gender')
        smokingPreference = request.form.get('smoking')
        alcoholPreference = request.form.get('alcohol')
        additionalPreference = request.form.get('additional-preferences')

        #Accomodation Preferences
        accomodationType = request.form.get('accommodation-type')
        roomSharing = request.form.get('room-sharing')
        mealPreference = request.form.get('meal')

        file = request.files.get('tripImage')

        if not file or not self.allowed_file(file.filename):
            return jsonify({"error": "Invalid or missing image"}), 400
        
        # Secure file name and save
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_TRIPS'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        if not all([title, destination, specificLocation, startDate, endDate, description, userId, travelStyle, budget, activities, pace, ageRange, groupSize, communicationStyle, genderPreference, smokingPreference, alcoholPreference, additionalPreference, accomodationType, roomSharing, mealPreference]):
            return jsonify({ "error":"Please fill in all required fields!" }), 400

        # trip = {
        #     "_id": uuid.uuid4().hex,
        #     "title": title,
        #     "destination": destination,
        #     "startDate": startDate,
        #     "endDate": endDate,
        #     "description": description,
        #     "hostID": userId
        # }

        trip = {
            "_id": uuid.uuid4().hex,
            "hostID": userId,
            "title": title,
            "destination": destination,
            "specificLocation": specificLocation,
            "startDate": datetime.strptime(startDate, "%Y-%m-%d"),
            "endDate": datetime.strptime(endDate, "%Y-%m-%d"),
            "description": description,
            "image": f"/{upload_path}",

            "travelPreferences": {
                "travelStyle": travelStyle,
                "budget": budget,
                "activities": activities
            },

            "companionPreferences": {
                "ageRange": ageRange,
                "groupSize": groupSize,
                "communicationStyle": communicationStyle,
                "smokingPreference": smokingPreference,
                "alcoholPreference": alcoholPreference,
                "genderPreference": genderPreference,
                "otherRequirements": additionalPreference
            },

            "logistics": {
                "accommodationType": accomodationType,
                "roomSharing": roomSharing,
                "mealPreference": mealPreference,
            },

            "createdAt": datetime.now(),
            "joinedUsers": [],
            "joinRequests": []
        }

        if trips.insert_one(trip):
            return jsonify(trip), 200

        return jsonify({ "error":"Trip creation failed!" }), 400

    def findTrip(self):
        userId = session['user']['_id']
        recommended = hybrid_recommend(userId)
        results = []

        for trip in recommended:
            r = self.getTripById(trip[0]["_id"])
            host = self.getUserById(r["hostID"])

            host_name = f"{host.get('first_name', '')} {host.get('last_name', '')}"
            
            ratingData = API().getRatingSummary(host.get('_id',''))
            host_avgRating = round(ratingData["averageRating"], 1)
            host_ratingCount = ratingData["ratingCount"]

            r["hostName"] = host_name
            r["hostAvgRating"] = host_avgRating
            r["hostRatingCount"] = host_ratingCount

            results.append(r)

        return jsonify(results)
    
    def searchTrips(self):
        data = request.json
        search = search_trips(data)
        results = []

        for trip in search:

            host = self.getUserById(trip["hostID"])

            host_name = f"{host.get('first_name', '')} {host.get('last_name', '')}"
            host_image = host.get('image', '')

            ratingData = API().getRatingSummary(host.get('_id',''))
            host_avgRating = round(ratingData["averageRating"], 1)
            host_ratingCount = ratingData["ratingCount"]
            
            trip["hostName"] = host_name
            trip["hostImage"] = host_image
            trip["hostAvgRating"] = host_avgRating
            trip["hostRatingCount"] = host_ratingCount

            results.append(trip)

        return jsonify(results)

    def joinTripRequest(self, tripId):
        user_id = session['user']['_id']
        file = request.files.get("idProof")

        if not file:
            return jsonify({"error": "No ID proof uploaded"}), 400

        filename = secure_filename(f"{user_id}_{file.filename}")
        proof_path = os.path.join(current_app.config["UPLOAD_FOLDER_IDPROOFS"], filename)
        os.makedirs(os.path.dirname(proof_path), exist_ok=True)
        file.save(proof_path)

        request_entry = {
            "userId": user_id,
            "idProofPath": f"/{proof_path}",
            "status": "pending",
            "requestedOn": datetime.now()
        }

        db.trips.update_one(
            {"_id": tripId},
            {"$addToSet": {"joinRequests": request_entry}}
        )

        return jsonify({"message": "Join request submitted. Awaiting host approval."})

    def approveRequest(self, tripId, userId):
        db.trips.update_one(
            {"_id": tripId, "joinRequests.userId": userId},
            {
                "$set": {"joinRequests.$.status": "approved","joinRequests.$.statusUpdatedOn": datetime.now()},
                "$addToSet": {"joinedUsers": userId}
            }
        )
        return "Approved", 200

    def rejectRequest(self, tripId, userId):
        db.trips.update_one(
            {"_id": tripId, "joinRequests.userId": userId},
            {
                "$set": {"joinRequests.$.status": "rejected","joinRequests.$.statusUpdatedOn": datetime.now()}
            }
        )
        return "Rejected", 200

    def getTripById(self, tripId):
        return db.trips.find_one({'_id':tripId})
    
    def getUserById(self, userId):
        return db.users.find_one({'_id':userId})