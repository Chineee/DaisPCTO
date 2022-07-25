from flask import Blueprint, render_template, url_for, redirect, flash, abort
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.models import *
from DaisPCTO.db import get_course_by_id
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
    course_hours = IntegerField("Numero di ore totali del corso", validators=[NumberRange(min=1, message="L'ammontare delle ore deve essere di almeno 1!")], default=1)

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
            #1) aggigungi il corso al database
            #2) Aggiungi la relazione con il professore che l'ha creato
            #3) AGGIUNGI FUNZIONE PER ADDARE STUDENTI AL DATABASE (HASSNTFEEDBACK = FALSE DI DEFAULT)
            return "ok" 
        else:
            form.course_id.errors.append("Corso già esistente")
       
    return render_template("courses.html", form=form, user=current_user, is_professor=current_user.hasRole("Professor"))
    
    