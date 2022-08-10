from flask import Flask, render_template, session as flasksession, redirect, url_for, request
from flask_login import current_user, LoginManager
from DaisPCTO.db import get_user_by_id, extestone, get_schools_with_name
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask.json import jsonify
import base64 
import io
import qrcode

# from flask_admin import Admin, expose, BaseView, AdminIndexView
# from flask_admin.contrib.sqla import ModelView

# class UserModelView(AdminIndexView):
#     def is_accessible(self):
#         return True


# class MyView(ModelView):
#     def is_accessible(self):
#         return False


# def is_professor(user):
#     if not current_user.is_authenticated:
#         return False
#     return current_user.hasRole("Professor")


def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = "mysecretkey"
    csrf = CSRFProtect()
    csrf.init_app(app)
    Bootstrap(app)
       
    login_manager = LoginManager()
    login_manager.login_view = "auth_blueprint.login"
    login_manager.init_app(app)
    login_manager.login_message = "Devi accedere per poter visitare questa pagina!"

    # admin = Admin(app, index_view=UserModelView())

    # admin.add_view(MyView(User, Session()))

    @app.route('/action/get/schools')
    def give_school_attribute():
        '''
        FUNZIONE CHE VIENE CHIAMATA DAL SERVER PER OTTENERE INFORMAZIONI SULLE SCUOLE DATO IL LORO NOME
        '''
        name = request.args.get("name")
        if name == "":
            return jsonify({"success" : False})
        l = get_schools_with_name(name.upper())

        

        res = []

        for school in l:
            school_add = {}
            school_add["School_id"] = school.SchoolID
            school_add["School_name"] = school.SchoolName
            school_add["School_city"] = school.City
            school_add["School_region"] = school.Region
            school_add["School_address"] = school.Address

            if (school.SchoolID == 28397):
                print(school.Address)
            
            if (school.SchoolID == 26253):
                print(school.Address)
            
            res.append(school_add)
    
   
        return jsonify({"success" : True, "result" : res})

    @app.route('/test')
    def test():
        extestone()
        return ""

    @app.route("/")
    def home():            
        return render_template("page.html", user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))
        
    @login_manager.user_loader
    def load_user(UserID):   
        return get_user_by_id(UserID)

    @app.errorhandler(404)
    def page_not_found(e):
        return "err", 404

    @app.before_request
    def check_csrf():
        csrf.protect()

    @app.template_filter("to_minutes")
    def to_minutes(time):
        return time.total_seconds()/60

    @app.template_filter("get_completed_percentage")
    def get_completed_percentage(user_minutes, needed_hour):
        if needed_hour == 0:
            return 100
        perc = ( user_minutes/(needed_hour*60) ) * 100
        return perc if perc <= 100 else 100

    @app.template_filter("convert_to_integer")
    def convert_to_integer(number):
        return int(number)

    @app.template_filter("can_be_booked")
    def can_be_booked(lesson, number_reservation):
        # print(lesson.LessonID)
        # print(f'{number_reservation[2].Reserv} PRENOTAZIONI SU {number_reservation[2].Seats}')
        # print(type(number_reservation))
        # print(number_reservation)
        for booked in number_reservation:
            # print(f'Prenotazioni == {booked.Reserv} ==> Posti disponibili == {booked.Seats} ===> ID LEZIONE == {booked.LessonID}')
            if booked.LessonID == lesson.LessonID:
                # print(f'Prenotazioni == {booked.Reserv} ==> Posti disponibili == {booked.Seats} ===> ID LEZIONE == {booked.LessonID}')
                if booked.Reserv >= booked.Seats:
                    return (False, booked.Reserv)
                return (True, booked.Reserv)

    @app.template_filter("convert_token_to_qrcode")
    def convert_token_to_qrcode(token):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(token)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        return img
    

    app.register_error_handler(404, page_not_found)


    from DaisPCTO.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from DaisPCTO.courses import courses as courses_blueprint 
    app.register_blueprint(courses_blueprint, url_prefix="/courses")

    from DaisPCTO.lessons import lessons as lessons_blueprint 
    app.register_blueprint(lessons_blueprint)
    
    return app