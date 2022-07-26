from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.models import *
from DaisPCTO.db import add_course, get_course_by_id, can_professor_modify, \
    get_user_by_id, get_professor_by_course_id, change_course_attr, \
    count_student, change_feedback, subscribe_course, \
    delete_subscription, is_subscribed
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, NumberRange

courses = Blueprint("courses_blueprint", __name__, template_folder="templates")

class AddCourse(FlaskForm):
    
    name = StringField("Nome *", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Nome"})
    course_id = StringField("ID Corso *", validators=[DataRequired(message="Campo richiesto")], render_kw = {"placeholder":"ID Corso"})
    description = TextAreaField("Descrizione", render_kw={"placeholder" : "Descrizione"})
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hour_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)


class ChangeInformationCourse(FlaskForm):
    name = StringField("Nome corso")
    description = TextAreaField("Descrizione")
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hour_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)

    changeSubmit = SubmitField()
    submit = SubmitField()

    subscribe = SubmitField()

    def validate(self):
        
        if not current_user.is_authenticated:
            return False
        if not current_user.hasRole("Professor"):
            return False
        return True

@courses.route('/', methods=['GET', 'POST'])
def home_courses():
   pass

@courses.route('/private', methods=['GET', 'POST'])
def private():
    pass

@courses.route('/add', methods=['GET', 'POST'])
@role_required("Professor")
def add():
    form = AddCourse()
    if form.validate_on_submit():
        if get_course_by_id(form.course_id.data) is None:
            add_course(form)
            return redirect(url_for("home"))
        else:
            form.course_id.errors.append("Corso già esistente")
       
    return render_template("courses.html", form=form, user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))

@courses.route('/<coursePage>', methods=['GET', 'POST'])
def course(coursePage):

    # if request.method == "POST":
    #     if not current_user.is_authenticated or not current_user.hasRole("Professor"):
    #         abort(404)

    if get_course_by_id(coursePage.upper()) is None:
        abort(404)

    form = ChangeInformationCourse()
    
    if form.validate_on_submit():

        if form.submit.data:
            change_feedback(coursePage.upper())
        elif form.changeSubmit.data:
            change_course_attr(form, coursePage.upper())
    
    elif form.subscribe.data:
        print("registrato")


    print(current_user.get_id())
    print(is_subscribed(current_user.get_id(), coursePage.upper()))
    return render_template("coursePage.html", 
         is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
         course = get_course_by_id(coursePage.upper()), 
         canModify = can_professor_modify(current_user.get_id(), coursePage.upper()), 
         user = current_user,
         prof = get_professor_by_course_id(coursePage.upper()),
         form = form,
         subs = count_student(coursePage.upper()),
         iscritto = is_subscribed(current_user.get_id(), coursePage.upper()))
    #controlliamo chi sta accedendo
    #se è un prof che ha creato il corso o che fa parte della relazione facciamo comparire un bottone "modifica corso"
    #renderizza ad una pagina modifica corso accessibile solo ai prof che l'hanno modificata

@courses.route('/action/<issubbed>/<course>')
@login_required
def subs(issubbed, course):
    course = course.upper()

    if issubbed == "notsubbed":
        subscribe_course(current_user.get_id(), course)
    elif issubbed == "subbed":
        delete_subscription(current_user.get_id(), course)

    return redirect(url_for("courses_blueprint.course", coursePage=course))
