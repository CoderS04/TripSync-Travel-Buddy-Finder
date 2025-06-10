from flask import Flask, Blueprint
from backend.user.models import User

user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/signup', methods = ['POST'])
def signup():
    return User().signup()


@user_bp.route('/login', methods = ['POST'])
def login():
    return User().login()

@user_bp.route('/signout')
def signout():
    return User().signout()