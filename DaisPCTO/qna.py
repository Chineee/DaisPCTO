from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, jsonify
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
# from DaisPCTO.models import *
from DaisPCTO.db import get_questions_by_course, can_user_delete_post, delete_post
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired

QnA = Blueprint("qna_blueprint", __name__, template_folder="templates")

class AddPost(FlaskForm):
    text = TextAreaField("Post", validators=[DataRequired(message="Il post deve avere un testo!")], render_kw={"place-holder":"Scrivi qui il tuo post..."})
    ref_to = IntegerField("ID post di riferimento", render_kw={"place-holder" : "ID post di riferimento"})

class UpdatePost(FlaskForm):
    text = TextAreaField("Post", validators=[DataRequired(message="Il post deve avere un testo!")], render_kw={"place-holder":"Scrivi qui il tuo post..."})
    
    changeSubmit = SubmitField()

'''
    TODO: METTERE UN COUNTER PER I MI PIACE PER OGNI POST
'''

@QnA.route('/courses/<coursePage>/forum')
@login_required
def forum(coursePage):
    questions = get_questions_by_course(coursePage.upper())

    for i in questions:
        print(i.Text)

    return render_template("forum.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user = current_user,
                            questions = questions)

@QnA.route('/action/post/delete')
@login_required
def delete():
    post_id = request.args.get('postid')
    if can_user_delete_post(current_user.get_id(), post_id):
        delete_post(post_id)
    