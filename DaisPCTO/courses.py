from operator import contains
from flask import Blueprint, render_template, url_for, redirect, flash, abort, request, jsonify
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
# from DaisPCTO.models import *
from DaisPCTO.db import add_course, can_student_send_feedback, city_subscribed, gender_subscribed, get_course_by_id, can_professor_modify, get_user_by_email, \
    get_user_by_id, get_professor_by_course_id, change_course_attr, hours_attended, \
    count_student, change_feedback, subscribe_course, age_subscribed, \
    delete_subscription, add_professor_course, is_subscribed, get_courses_list, get_professor_courses, get_users_role, get_student_courses, send_certificate_to_students, get_student_certificates, type_school_subscribed, get_students_by_course
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length, NumberRange
import json

courses = Blueprint("courses_blueprint", __name__, template_folder="templates")

class AddCourse(FlaskForm):
    
    name = StringField("Nome *", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Nome"})
    course_id = StringField("ID Corso *", validators=[DataRequired(message="Campo richiesto")], render_kw = {"placeholder":"ID Corso"})
    description = TextAreaField("Descrizione", render_kw={"placeholder" : "Descrizione"})
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hour_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)

    def validate_course_id(self, course_id):
        if ' ' in course_id.data:
            raise ValidationError("L'id non può contenere spazi")


class ChangeInformationCourse(FlaskForm):
    name = StringField("Nome corso")
    description = TextAreaField("Descrizione")
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hour_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)

    changeSubmit = SubmitField()
    submit = SubmitField()

    subscribe = SubmitField()

@courses.route('/certificates')
@role_required("Student")
def certificate():
    certificates = get_student_certificates(current_user.get_id())

    return render_template("certificates.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user = current_user,
                            certificates = certificates,
                            roles = get_users_role(current_user.get_id())) 

@courses.route('/')
def home_courses():
   course_list = get_courses_list()

   return render_template("courses.html",
                          course_list = course_list,
                          is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                          user = current_user,
                          roles = get_users_role(current_user.get_id())
                         )
              
@courses.route('/subscriptions', methods=['GET', 'POST'])
@login_required
def private():
    is_professor = current_user.hasRole("Professor")

    courses_list = []
    if is_professor:
        courses_list = get_professor_courses(current_user.get_id())
    else:
        courses_list = get_student_courses(current_user.get_id())


    return render_template("courses_private.html",
                           is_professor = is_professor,
                           user = current_user,
                           course_list = courses_list,
                           roles = get_users_role(current_user.get_id())
                           )

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
       
    return render_template("addCourse.html", 
                            form=form,
                            user=current_user, 
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            roles = get_users_role(current_user.get_id()))

@courses.route('/<coursePage>', methods=['GET', 'POST'])
def course(coursePage):

    if get_course_by_id(coursePage.upper()) is None:
        abort(404)

    form = ChangeInformationCourse()
    can_modify = can_professor_modify(current_user.get_id(), coursePage.upper())

    if form.validate_on_submit() and can_modify:
        if form.submit.data:
            res = change_feedback(coursePage.upper())
            if res:
                send_certificate_to_students(coursePage.upper())
        elif form.changeSubmit.data:
            change_course_attr(form, coursePage.upper())

    return render_template("coursePage.html", 
         is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
         course = get_course_by_id(coursePage.upper()), 
         can_modify = can_modify, 
         user = current_user,
         prof = get_professor_by_course_id(coursePage.upper()),
         form = form,
         subs = count_student(coursePage.upper()),
         iscritto = is_subscribed(current_user.get_id(), coursePage.upper()),
         can_send = can_student_send_feedback(current_user.get_id(), coursePage.upper()),
         roles = get_users_role(current_user.get_id()))

"""
Funzione richiamata dagli studenti per iscriversi o disiscriversi dai corsi, la route viene richiamata dopo l'avvenuta pressione di un bottone nella
pagina principale del corso
"""
@courses.route('/action/<course>')
@role_required("Student")
def subs(course):
    course = course.upper()
    issubbed = request.args.get("sub")

    if issubbed == 'false':
        subscribe_course(current_user.get_id(), course)
        
    elif issubbed == 'true':
        delete_subscription(current_user.get_id(), course)
        last_page = request.args.get("lastpage")
        if last_page == 'coursespage':
            return redirect(url_for("courses_blueprint.private"))

    return redirect(url_for("courses_blueprint.course", coursePage=course))


@courses.route('/<coursePage>/students')
@role_required("Professor")
def students_list(coursePage):

    if not can_professor_modify(current_user.get_id(), coursePage.upper()):
        abort(401)

    students_list_info = get_students_by_course(coursePage.upper())

    return render_template("student_list_info.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user = current_user,
                            students = students_list_info,
                            course = get_course_by_id(coursePage.upper()),
                            roles = get_users_role(current_user.get_id()))

"""
Il professore che crea un corso, potrà anche aggiungere dei collaboratori che avranno accesso a tale pagina.
"""                     
@courses.route('/<coursePage>/addprof', methods=['POST'])
@role_required("Professor")
def addprof(coursePage):
    if not can_professor_modify(current_user.get_id(), coursePage.upper()):
        abort(401)
        
    user = get_user_by_email(request.args.get("email"))
    if "Professor" not in get_users_role(user.get_id()):
        return jsonify({"success" : False})

    add_professor_course(coursePage.upper(), user.get_id())
    
    return jsonify({"success" : True, "name" : user.Name, "surname" : user.Surname})

#pagina di demografica contenente grafici statistici con informazioni utili
@courses.route('/<coursePage>/demographics')
@role_required("Professor")
def demographics(coursePage):

    if not can_professor_modify(current_user.get_id(), coursePage.upper()):
        abort(404)

    no_student = False

    if count_student(course_id=coursePage.upper()) == 0:
        no_student = True

    return render_template("demographics.html",
                            is_professor = True,
                            user = current_user,
                            course_id = coursePage.upper(),
                            no_student = no_student,
                            roles = get_users_role(current_user.get_id()))

#ritornana un dizionario contenente il numero di studenti per ogni tipo di gender inserito nel database (m, f, nb, o)
@courses.route('/action/get/student_gender')
@role_required("Professor")
def get_student_gender():

    course_id = request.args.get("course_id").upper()

    g = gender_subscribed(course_id)
    return jsonify({"success" : True, "Male" : g.Male, "Female" : g.Female, "Non-Binary": g.NonBinary, "Other" : g.Other})

#ritorniamo un dizionario contenente il numero di studenti per ogni regione
@courses.route('/action/get/region')
@role_required("Professor")
def get_student_region():

    course_id = request.args.get("course_id").upper()
    c = city_subscribed(course_id)
       
    res = {}
    with open("province.json") as f:
        data = json.load(f)
        for city in c:
            for i in data:
                if i["nome"].upper() == city.City:
                    if i["regione"] not in res:
                        res[i["regione"]] = 1
                    else:
                        res[i["regione"]] += 1
    
    return jsonify({"success" : True, "Regioni" : res, "Total" : len(c)})

@courses.route('/action/get/school')
@role_required("Professor")
def get_student_school():
    course_id=request.args.get("course_id").upper()
    type_schools = type_school_subscribed(course_id)
    
    return jsonify({"success" : True, "Liceo" : type_schools.Liceo, "Tecnico" : type_schools.Tecnico, "Professionale" : type_schools.Professionale, "Altro" : type_schools.Altro})

"""
ritorna un dizionario contenente quanti studenti hanno una determinata età, data un'età minima ed un età massima.
considerando che siamo in un contesto di alternanza scuola lavoro, la differnza di età fra minima e massima degli studenti non sarà mai troppo grande
l'età viene banalmente calcolata usando la data di nascita e la data corrente
"""
@courses.route('/action/get/mean_age')
@role_required("Professor")
def get_age_student():
    course_id = request.args.get("course_id").upper()
    ages = age_subscribed(course_id)
    
    def calculate_age(born):
        from datetime import date
        today = date.today()
        return today.year - born.year - ((today.month, today.day) < (born.month, born.day)) 
    
    res = {}
    minim = -1
    maxi = 0
    for date in ages:
        if date.birthDate is not None:
            age = calculate_age(date.birthDate)
            if age < minim or minim == -1:
                minim = age
            if age > maxi:
                maxi = age
            if age not in res:
                res[age] = 1
            else:
                res[age] += 1
    
    return jsonify({"success" : True, "ages" : res, "len" : len(res), "min" : minim, "max" : maxi})

"""
Può essere utile per il prof sapere quanto gli studenti stanno seguendo le lezioni, abbiamo deciso di fornire dati basati sulle ore piuttosto che sul numero
di lezioni, per dare un'idea al professore di quanti studenti hanno ottenuto o stanno per ottenere il certificato di partecipazione al corso, tutti i gruppi 
sono ovviamente disgiunti, quindi se uno studente A appartiene al gruppo di studenti che hanno seguito 10 ore, NON potrà appartenere ai gruppi di studenti con 
ore inferiori.

NB : Quando avviene una relazione Studente-Lezione, allo studente saranno aggiunte TUTTE le ore per quella lezione, non potrà mai accadere un caso in cui
ad uno studente vengano aggiunte solo metà delle ore o solo parte delle ore di una lezione.
"""
@courses.route('/action/get/hours_attended')
@role_required("Professor")
def get_hours_attended():
    course_id = request.args.get("course_id").upper()
    hours = hours_attended(course_id)

    res = {}

    for i in hours:
        if i.Hours.total_seconds()/3600 not in res:
            res[i.Hours.total_seconds()/3600] = 1
        else:
            res[i.Hours.total_seconds()/3600] += 1

    res = {k: v for k, v in sorted(res.items(), key=lambda item: item[1])}  
    
    return jsonify({"success" : True, "hours_attended" : res})