# app/__init__.py

from flask import Flask
from flask_login import LoginManager
from app.models import db
from app.models import User  # make sure this is correct
import os 

login_manager = LoginManager()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def create_app():
    # Set the static_folder path explicitly (adjust if needed)
    static_folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static')
    static_folder_path = os.path.abspath(static_folder_path)

    # Initialize the Flask app with the correct static folder path
    app = Flask(__name__, static_folder=static_folder_path)
    app.config.from_object('config')  # loads from config.py
    app.debug = True  #
    db.init_app(app)
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'  # redirect to login if not authenticated

    # Register your blueprints
    from app.routes.auth_routes import auth_bp
    from app.routes.student_routes import stud_bp
    from app.routes.faculty_routes import faculty_bp
    app.register_blueprint(faculty_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(stud_bp)


    return app

