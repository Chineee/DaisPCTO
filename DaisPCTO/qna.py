from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, jsonify
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import get_course_by_id, get_questions_by_course, is_user_owner_post, delete_post, get_answers_by_question_id, add_post, update_post, get_users_role
from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField
from wtforms.validators import DataRequired

QnA = Blueprint("qna_blueprint", __name__, template_folder="templates")

class AddPost(FlaskForm):
    text = TextAreaField("Post", validators=[DataRequired(message="Il post deve avere un testo!")], render_kw={"placeholder":"Scrivi qui il tuo post..."})
    ref_to = IntegerField("ID post di riferimento", render_kw={"placeholder" : "ID post di riferimento"})

"""
Pagina di forum del corso, con domande e tutte le risposte alle relative domande.
Disponibili azioni di Aggiunta post, che può essere una domanda "madre" oppure una risposta ad una domanda madre, questo fatto viene controllato
dal campo "refto" del form definito
"""
@QnA.route('/courses/<coursePage>/forum', methods=['GET', 'POST'])
@login_required
def forum(coursePage):
    form = AddPost()

    if form.validate_on_submit():
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
                            form=form,
                            course = get_course_by_id(coursePage.upper()),
                            roles = get_users_role(current_user.get_id()))

"""
Route richiamata da procedura ajax per fare un update di un post. In caso il nuovo post sia una stringa vuota, il post sarà eliminato (Esattamente come funziona con 
Discord)
"""
@QnA.route('/action/post/update', methods=['POST'])
@login_required
def update():
    post_id = request.args.get('id')
    if is_user_owner_post(current_user.get_id(), post_id): #viene controllato se chi richiede l'azione è "padrone" del post target
        txt = request.form['text']
        if len(txt) == 0:
            delete_post(post_id)
            return jsonify({"success" : "deleted"})
        elif update_post(txt, post_id):
            return jsonify({"success" : True})
    
    return jsonify({"success" : False})
