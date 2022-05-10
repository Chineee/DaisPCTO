from flask import Flask 
from flask import *

def create_app():
    app = Flask(__name__)
    from DaisPCTO.auth import auth as auth_blueprint 
    app.register_blueprint(auth_blueprint)
    return app