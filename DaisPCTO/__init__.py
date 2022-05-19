from flask import Flask, render_template
from flask_login import current_user, login_manager, LoginManager
from DaisPCTO.auth import login
from DaisPCTO.db import get_user_by_id
from flask_bootstrap import Bootstrap
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from DaisPCTO.db import Session

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "ediolognomomongoloide"
    app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
    Bootstrap(app)

    # admin=Admin(app)
    # from DaisPCTO.models import User
    # admin.add_view(ModelView(User, Session()))
        
    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.init_app(app)

    @app.route("/")
    def home():
        return render_template("page.html", user=current_user)

    @login_manager.user_loader
    def load_user(UserID):
        return get_user_by_id(UserID)

    from DaisPCTO.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    return app


    