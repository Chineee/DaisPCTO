from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
# from DaisPCTO.models import *
from DaisPCTO.db import add_course, get_course_by_id, can_professor_modify, \
    get_user_by_id, get_professor_by_course_id, change_course_attr, \
    count_student, change_feedback, subscribe_course, \
    delete_subscription, is_subscribed
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


class ChangeInformationCourse(FlaskForm):
    name = StringField("Nome corso")
    description = TextAreaField("Descrizione")
    max_students = IntegerField("Numero massimo di studenti", validators=[NumberRange(min = 0, message="Non puoi inserire un numero di studenti negativo")], default=0)
    min_hour_certificate = IntegerField("Ore minime per ottenere il certificato", validators=[NumberRange(min=0, message="Non puoi inserire un numero di ore negative")], default=0)

    changeSubmit = SubmitField()
    submit = SubmitField() #

    subscribe = SubmitField()

@courses.route('/', methods=['GET', 'POST'])
def home_courses():
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
       
    return render_template("courses.html", 
                            form=form,
                            user=current_user, 
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))

@courses.route('/<coursePage>', methods=['GET', 'POST'])
def course(coursePage):


    if get_course_by_id(coursePage.upper()) is None:
        abort(404)

    form = ChangeInformationCourse()
    can_modify = can_professor_modify(current_user.get_id(), coursePage.upper())

    if form.validate_on_submit() and can_modify:
        print("hello")
        if form.submit.data:
            change_feedback(coursePage.upper())
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
         iscritto = is_subscribed(current_user.get_id(), coursePage.upper()))
    #controlliamo chi sta accedendo
    #se è un prof che ha creato il corso o che fa parte della relazione facciamo comparire un bottone "modifica corso"
    #renderizza ad una pagina modifica corso accessibile solo ai prof che l'hanno modificata

@courses.route('/action/<course>')
@role_required("Student")
def subs(course):
    course = course.upper()
    issubbed = request.args.get("sub")

    if issubbed == 'false':
        subscribe_course(current_user.get_id(), course)
        
    elif issubbed == 'true':
        delete_subscription(current_user.get_id(), course)

    return redirect(url_for("courses_blueprint.course", coursePage=course))


""""

CREATE TRIGGER max_students_check
BEFORE INSERT ON StudentsCourses
FOR EACH ROW EXECUTE FUNCTION max_students_check_func()

CREATE FUNCTION max_students_check_func() RETURNS TRIGGER
BEGIN
    IF ( (
        SELECT COUNT(*)
        FROM StudentCourses sc JOIN Courses c USING(CourseID)
        WHERE NEW.CourseID = c.CourseID) >= (SELECT c.MaxStudents
                                            FROM Courses c
                                            WHERE c.CourseID = NEW.CourseID) AND (SELECT c3."MaxStudents"
                                                                                  FROM "public"."Courses" AS c3 
                                                                                  WHERE c3."CourseID" = NEW."CourseID") > 0)) THEN RETURN NULL;
    END IF
    RETURN NEW;
END


"""