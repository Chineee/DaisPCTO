from symtable import SymbolTableFactory
from flask import Blueprint, jsonify, render_template, url_for, redirect, flash, abort, request, logging
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import get_course_by_id, can_student_send_feedback, send_feedback
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DateField, SelectField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField, TimeField
from wtforms.validators import DataRequired, ValidationError

feedback = Blueprint("feedbacks_blueprint", __name__, template_folder = "templates")

class SendFeedback(FlaskForm):
    course_grade = IntegerField("Voto al Corso", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Voto al corso"})
    teacher_grade = IntegerField("Voto all'insegnante", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Voto all'insegnante"})
    comments = TextAreaField("Commenti generali", render_kw={"placeholder":"Commenta"})

    def validate_course_grade(self, course_grade):
        pass

    
@feedback.route('/courses/<coursePage>/feedback', methods=['get', 'post'])
@role_required("Student")
def feedback_home(coursePage):
    if not get_course_by_id(coursePage.upper()).OpenFeedback:
        abort(404)
    form = SendFeedback()
    can_send = can_student_send_feedback(current_user.get_id(), coursePage.upper())

    if can_send and form.validate_on_submit():
        send_feedback(form, coursePage.upper())

    return render_template("feedback.html",
                           is_professor = False,
                           user = current_user,
                           form = form
                           )

