from flask import Flask 

from flask_bootstrap import Bootstrap


def create_app():
    app = Flask(__name__)
    Bootstrap(app)
    app.config['SECRET_KEY'] = "ediolognomomongoloide"
    from DaisPCTO.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    return app