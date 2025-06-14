from flask import Flask, jsonify, request, session, redirect, current_app, flash
from passlib.hash import pbkdf2_sha256
import uuid

from werkzeug.utils import secure_filename
import os

from flask_mail import Message

from random import randint

from extensions import db,mail

class User:

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def start_session(self, user):
        del user['password']
        session['logged_in'] = True
        session['user'] = user
        db.users.update_one({'_id': user['_id']}, {'$set': {'isOnline': True}})
        return jsonify(user), 200

    def signup(self):
        users = db["users"]
        
        # Get form data
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
        city = request.form.get('city')
        country = request.form.get('country')
        birthdate = request.form.get('birthdate')
        gender = request.form.get('gender')

        file = request.files.get('userImage')
        if not file or not self.allowed_file(file.filename):
            return jsonify({"error": "Invalid or missing image"}), 400
        
        # Secure file name and save
        filename = secure_filename(file.filename)
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER_USERS'], filename)
        os.makedirs(os.path.dirname(upload_path), exist_ok=True)
        file.save(upload_path)

        travel_style = request.form.get('travel-style')
        interests = request.form.getlist('interests[]')
        agreed = request.form.get('terms')

        # Basic validation
        if not all([first_name, last_name, email, password, confirm_password, country, birthdate, travel_style, agreed]):
            return jsonify({"error": "Please fill in all required fields."}), 400

        if password != confirm_password:
            return jsonify({"error": "Passwords do not match."}), 400

        if users.find_one({ "email": email }):
            return jsonify({"error": "This email is already in use!"}), 400

        user = {
            "_id": uuid.uuid4().hex,
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": pbkdf2_sha256.encrypt(password),
            "city": city,
            "country": country,
            "birthdate": birthdate,
            "gender": gender,
            "image": f"/{upload_path}",
            "bio": "",
            "travel_style": travel_style,
            "interests": interests,
            "agreed_to_terms": True,
            "isOnline": False,
            "connections": [],
            "connectionRequests": [],
            "completedTrips": [],
            "joinedTrips": []
        }

        otp = str(randint(100000, 999999))
        session['pending_user'] = {
            "data": user,
            "otp": otp,
            "email": email
        }

        msg = Message("Your TripSync Verification Code 🔐", recipients=[email])
        msg.body = f"""
        Hi {first_name},

        Your One-Time Password (OTP) for verifying your TripSync account is:

        🔑 {otp}

        This code is valid for the next 10 minutes.
        Please do not share it with anyone.

        If you didn’t request this, feel free to ignore this email.

        Safe travels,
        The TripSync Team 🌍
        """
        mail.send(msg)

        return jsonify({"redirect": '/user/verify-otp'})
    
    def verifyOTP(self, otp):

        pending = session.get("pending_user")

        if not pending:
            return "Session expired. Please sign up again.", 400

        if str(otp) == pending["otp"]:
            users = db["users"]
            user = pending['data']
            
            users.insert_one(user)

            msg = Message("Welcome to TripSync – Your Journey Starts Here! 🌍✈️", recipients=[user['email']])
            msg.body = f"""Hi {user['first_name']} {user['last_name']},

            Welcome to TripSync – we're thrilled to have you on board! 🌟
            Whether you're planning your next big adventure or looking to meet like-minded travel buddies, you're in the right place.

            Here’s what you can do next:

            ✨ Create or join amazing trips

            🤝 Find travel partners who match your vibe

            📍 Explore destinations based on your interests

            We’re all about making travel more fun, meaningful, and connected. So go ahead, complete your profile, and start exploring the world with companions who truly get you.

            Need help getting started? Just reply to this message—we’re always here for you.

            Happy travels,
            The TripSync Team 🌍"""
            
            mail.send(msg)

            session.pop("pending_user")
            
            self.start_session(user)
            
            return jsonify({"redirect": "/login"}), 200

        return jsonify({"error":"Invalid OTP. Try again."}), 400


    def login(self):
        users = db["users"]

        user = users.find_one({ "email":request.form.get('email') })

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
            return self.start_session(user)

        return jsonify({ "error":"Invalid Login Credentials!" }), 401

    def signout(self):
        db.users.update_one({'_id': session['user']['_id']}, {'$set': {'isOnline': False}})
        session.clear()
        return redirect('/')
    
    def sendConnectionRequest(self, buddyId):
        users = db["users"]
        if buddyId not in session['user']['connections']:
            if users.update_one({"_id":buddyId}, {"$addToSet": {"connectionRequests": session['user']['_id']}}):
                return jsonify("Connection requst sent!"), 200
        else:
            return jsonify("Already connected!"), 200
        
        return jsonify("Something went wrong!"), 501
    
    def updateProfile(self, data):
        user_id = session['user']['_id']

        update = {
            "first_name": data.get("first_name", ""),
            "last_name": data.get("last_name", ""),
            "city": data.get("location", "").split(",")[0].strip(),
            "country": data.get("location", "").split(",")[-1].strip(),
            "travel_style": data.get("travel_style", "")
        }

        db.users.update_one({"_id": user_id}, {"$set": update})
        session['user'].update(update)
        return jsonify({"success": True})
    
    def updateBio(self, data):
        user_id = session['user']['_id']

        update = {
            "bio": data.get("bio", "")
        }

        db.users.update_one({'_id': user_id}, {"$set": update})
        session['user'].update(update)
        return jsonify({"success": True}), 200