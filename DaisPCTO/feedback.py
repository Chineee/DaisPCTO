from symtable import SymbolTableFactory
from flask import Blueprint, jsonify, render_template, url_for, redirect, flash, abort, request, logging
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import can_professor_modify, get_course_by_id, can_student_send_feedback, send_feedback, feedback_comments, avg_feedback
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

    
@feedback.route('/courses/<coursePage>/feedback', methods=['get', 'post'])
@role_required("Student")
def feedback_home(coursePage):
    if not get_course_by_id(coursePage.upper()).OpenFeedback:
        abort(404)
    form = SendFeedback()
    can_send = can_student_send_feedback(current_user.get_id(), coursePage.upper())
    print(can_send)

    if can_send and form.validate_on_submit():
        send_feedback(form, coursePage.upper())

    return render_template("feedback.html",
                           is_professor = False,
                           user = current_user,
                           form = form
                           )


@feedback.route('/courses/<coursePage>/get_feedback')
@role_required("Professor")
def get_feedback(coursePage):
    if not can_professor_modify(current_user.get_id(), coursePage.upper()):
        abort(401)

    h = feedback_comments(coursePage.upper())
    print(h)

    return render_template("get_feedback.html",
                            is_professor = True,
                            user = current_user,
                            comments = feedback_comments(coursePage.upper()),
                            avg_grades = avg_feedback(coursePage.upper()))