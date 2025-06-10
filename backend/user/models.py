from flask import Flask, jsonify, request, session, redirect, current_app
from passlib.hash import pbkdf2_sha256
import uuid

from werkzeug.utils import secure_filename
import os

from extensions import db

class User:

    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    def allowed_file(self, filename):
        return '.' in filename and filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS

    def start_session(self, user):
        del user['password']
        print("Starting session.")
        session['logged_in'] = True
        session['user'] = user
        return jsonify(user), 200

    def signup(self):
        users = db["users"]
        
        # Get form data
        first_name = request.form.get('first-name')
        last_name = request.form.get('last-name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm-password')
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
            "country": country,
            "birthdate": birthdate,
            "gender": gender,
            "image": f"/{upload_path}",
            "travel_style": travel_style,
            "interests": interests,
            "agreed_to_terms": True
        }

        if users.insert_one(user):
            return self.start_session(user)

        return jsonify({"error": "Signup failed"}), 400

    def login(self):
        users = db["users"]

        user = users.find_one({ "email":request.form.get('email') })

        if user and pbkdf2_sha256.verify(request.form.get('password'), user['password']):
                return self.start_session(user)

        return jsonify({ "error":"Invalid Login Credentials!" }), 401

    def signout(self):
        session.clear()
        return redirect('/')