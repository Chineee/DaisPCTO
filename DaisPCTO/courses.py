from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.models import *
from DaisPCTO.db import add_course, get_course_by_id, can_professor_modify, get_user_by_id, get_professor_by_course_id, change_course_attr, count_student
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, NumberRange

courses = Blueprint("courses_blueprint", __name__, template_folder="templates")

class AddCourse(FlaskForm):
    
    name = StringField("Nome *", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Nome"})
    course_id = StringField("ID Corso *", validators=[DataRequired(message="Campo richiesto")], render_kw = {"placeholder":"ID Corso"})
    description = TextAreaField("Descrizione", render_kw={"placeholder" : "Descrizione"})
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hours_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)


class ChangeInformationCourse(FlaskForm):
    name = StringField("Nome corso")
    description = TextAreaField("Descrizione")
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hours_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)

    def validate(self):
        
        if not current_user.is_authenticated:
            return False
        if not current_user.hasRole("Professor"):
            return False
        return True

@courses.route('/', methods=['GET', 'POST'])
def home():
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


    form = ChangeInformationCourse()

    if form.validate_on_submit():
        print("ok")
        #change_course_attr(form)
    
    return render_template("coursePage.html", 
         is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
         course = get_course_by_id(coursePage), 
         canModify = can_professor_modify(current_user.get_id(), coursePage), 
         user = current_user,
         prof = get_professor_by_course_id(coursePage),
         form = form,
         subs = count_student(coursePage))
    #controlliamo chi sta accedendo
    #se è un prof che ha creato il corso o che fa parte della relazione facciamo comparire un bottone "modifica corso"
    #renderizza ad una pagina modifica corso accessibile solo ai prof che l'hanno modificata
    

@courses.route('/<coursePage>/modify')
@role_required("Professor")
def modify(coursePage):
    if can_professor_modify(current_user.get_id(), coursePage):
        course = get_course_by_id(coursePage)
        return f'{course.Name} {course.maxStudents} {course.hasfeedback}'

