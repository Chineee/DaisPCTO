from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, jsonify
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
# from DaisPCTO.models import *
from DaisPCTO.db import get_questions_by_course, can_user_delete_post, delete_post, get_answers_by_question_id, add_post
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired

QnA = Blueprint("qna_blueprint", __name__, template_folder="templates")

class AddPost(FlaskForm):
    text = TextAreaField("Post", validators=[DataRequired(message="Il post deve avere un testo!")], render_kw={"placeholder":"Scrivi qui il tuo post..."})
    ref_to = IntegerField("ID post di riferimento", render_kw={"placeholder" : "ID post di riferimento"})

class UpdatePost(FlaskForm):
    text = TextAreaField("Post", validators=[DataRequired(message="Il post deve avere un testo!")], render_kw={"placeholder":"Scrivi qui il tuo post..."})
    
    changeSubmit = SubmitField()

'''
    TODO: METTERE UN COUNTER PER I MI PIACE PER OGNI POST
'''


@QnA.route('/courses/<coursePage>/forum', methods=['GET', 'POST'])
@login_required
def forum(coursePage):

    form = AddPost()

    form2 = UpdatePost()


    if form.validate_on_submit():
        print('aassdasa')
        add_post(form, coursePage.upper())
        return redirect(url_for("qna_blueprint.forum", coursePage=coursePage.upper()))

    questions = get_questions_by_course(coursePage.upper())
    
    qna = []

    for i in range(len(questions)):
        answers = get_answers_by_question_id(questions[i].TextID)
        qna_element = {"question" : questions[i], "answers" : answers}
        qna.append(qna_element)
        

    return render_template("forum.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user = current_user,
                            qna = qna,
                            form=form)

@QnA.route('/action/post/delete')
@login_required
def delete():
    post_id = request.args.get('postid')
    if can_user_delete_post(current_user.get_id(), post_id):
        delete_post(post_id)
    