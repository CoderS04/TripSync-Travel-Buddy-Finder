from flask import Blueprint, render_template, session, redirect, url_for

chat_bp = Blueprint('chat', __name__, url_prefix='/chat')

@chat_bp.route('/')
def chat_home():
    if 'user' not in session:
        return redirect('/login')

    return render_template('chatroom.html', user=session['user'])
