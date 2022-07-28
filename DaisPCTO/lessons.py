from ast import Add
from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import can_professor_modify, get_course_by_id, get_user_by_id, get_professor_by_course_id, \
    change_course_attr, add_lesson, get_lessons_by_course_id, delete_lesson
from flask_wtf import FlaskForm
from wtforms import StringField, DateField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField, TimeField
from wtforms.validators import DataRequired, ValidationError

lessons = Blueprint("lessons_blueprint", __name__, template_folder = "templates")

class AddOrDeleteLesson(FlaskForm):
    date = DateField("Data", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data"})
    start_time = TimeField("Orario di Inizio", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Inizio"})
    end_time = TimeField("Orario di Fine", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Fine"})
    topic = StringField("Argomento", render_kw={"placeholder":"Argomento"})
    # token = StringField("Token", render_kw={"placeholder":"Token"})
    is_dual = BooleanField("Duale", render_kw={"placeholder":"Duale"})
    classroom = StringField("Aula", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder" : "Aula"})

    lesson_id_to_delete = IntegerField()

    button_to_add = SubmitField()
    button_to_delete = SubmitField()



@lessons.route('/<coursePage>/lessons', methods=['GET', 'POST'])
def lessons_home(coursePage):
    form = AddOrDeleteLesson()

    can_modify = can_professor_modify(current_user.get_id(), coursePage.upper())

    list_lessons = get_lessons_by_course_id(coursePage.upper())

    if form.validate_on_submit() and can_modify:
        if form.button_to_add.data:
            if not add_lesson(form, coursePage.upper()): #se l'inserimento non va a buon fine, avvertiamo il chiamante
                form.classroom.errors.append("Aula già prenotata")
        elif form.button_to_delete.data: #form/button
            delete_lesson(form.lesson_id_to_delete.data)


    
    return render_template("lessons.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user=current_user,
                            can_modify=can_modify,
                            form=form,
                            list_lessons = list_lessons,
                            course=get_course_by_id(coursePage.upper())
                            )



@lessons.route("/<coursePage>/<lessonId>/action/subs")
@role_required("Student")
def lesson_subs(coursePage, lessonId):
    return "hello"