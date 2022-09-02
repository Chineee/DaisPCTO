import profile
from symtable import SymbolTableFactory
from flask import Blueprint, jsonify, render_template, url_for, redirect, flash, abort, request, logging
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import can_professor_modify, get_course_by_id, can_student_send_feedback, send_feedback, feedback_comments, avg_feedback, get_users_role
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DateField, SelectField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField, TimeField
from wtforms.validators import DataRequired, ValidationError

feedback = Blueprint("feedbacks_blueprint", __name__, template_folder = "templates")

class SendFeedback(FlaskForm):
    course_grade = IntegerField("Voto al Corso", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Voto al corso"})
    teacher_grade = IntegerField("Voto all'insegnante", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Voto all'insegnante"})
    comments = TextAreaField("Commenti generali", render_kw={"placeholder":"Commenta"})

    def validate_course_grade(self, course_grade):
        if course_grade.data < 0 or course_grade.data > 10:
            raise ValidationError();

    def validate_teacher_grade(self, teacher_grade):
        if teacher_grade.data < 0 or teacher_grade.data > 10:
            raise ValidationError();


"""la feedback home è una pagina accessibile solo dagli studenti solo quando il corso di riferimento ha i feedback disponibili (che sono apribili solo da uno dei prof
di riferimento), la pagina presenta un semplice form contenente due  valutazioni da 1 a 10 (obbligatorie) da dare al corso e al professore, ed un commento facoltative.
Tutti i voti e tutti i commenti risulteranno essere anonimi
"""

@feedback.route('/courses/<coursePage>/feedback', methods=['get', 'post'])
@role_required("Student")
def feedback_home(coursePage):
    if not get_course_by_id(coursePage.upper()).OpenFeedback:
        abort(404)
        
    form = SendFeedback()
    can_send = can_student_send_feedback(current_user.get_id(), coursePage.upper())

    if not can_send:
        abort(401)

    if form.validate_on_submit():
        send_feedback(form, coursePage.upper())
        return redirect(f'/courses/{coursePage}')

    return render_template("feedback.html",
                           is_professor = False,
                           user = current_user,
                           form = form,
                           roles = get_users_role(current_user.get_id())
                           )


"""
Concetto di questa route molto simile a quella spiegata sopra, ma il professore può visualizzare una media dei voti forniti dagli studenti ed una serie di commenti.
"""
@feedback.route('/courses/<coursePage>/get_feedback')
@role_required("Professor")
def get_feedback(coursePage):
    if not can_professor_modify(current_user.get_id(), coursePage.upper()):
        abort(401)

    return render_template("get_feedback.html",
                            is_professor = True,
                            user = current_user,
                            comments = feedback_comments(coursePage.upper()),
                            avg_grades = avg_feedback(coursePage.upper()),
                            roles = get_users_role(current_user.get_id()))