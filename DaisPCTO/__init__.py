from flask import Flask, render_template, session as flasksession, redirect, url_for, request
from flask_login import current_user, LoginManager
from DaisPCTO.db import get_user_by_id, extestone, Session, User
from flask_bootstrap import Bootstrap
import secrets
# from flask_admin import Admin, expose, BaseView, AdminIndexView
# from flask_admin.contrib.sqla import ModelView

# class UserModelView(AdminIndexView):
#     def is_accessible(self):
#         return True


# class MyView(ModelView):
#     def is_accessible(self):
#         return False
    
def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "mysecretkey"
    
    Bootstrap(app)
       
    login_manager = LoginManager()
    login_manager.login_view = "auth_blueprint.login"
    login_manager.init_app(app)
    login_manager.login_message = "Devi accedere per poter visitare questa pagina!"

    # admin = Admin(app, index_view=UserModelView())

    # admin.add_view(MyView(User, Session()))


    @app.route("/")
    def home():              
        return render_template("page.html", user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))

    @login_manager.user_loader
    def load_user(UserID):
        return get_user_by_id(UserID)

    # @app.route("/testone")
    # def testone():
    #     extestone()
    #     return "ok"


    from DaisPCTO.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from DaisPCTO.courses import courses as courses_blueprint 
    app.register_blueprint(courses_blueprint, url_prefix="/courses")
    
    return app