from flask import Flask, Blueprint, request, render_template
from backend.user.models import User

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/signup', methods = ['POST'])
def signup():
    return User().signup()

@user_bp.route("/verify-otp", methods=["GET", "POST"])
def verify_otp():
    if request.method == "POST":
        print("trying to verify otp")
        input_otp = request.form.get("otp")
        return User().verifyOTP(input_otp)

    print("trying to render template verify-otp.html")
    return render_template("verify-otp.html")

@user_bp.route('/login', methods = ['POST'])
def login():
    return User().login()

@user_bp.route('/signout')
def signout():
    return User().signout()