from symtable import SymbolTableFactory
from flask import Blueprint, jsonify, render_template, url_for, redirect, flash, abort, request, logging
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import add_multiple_lesson, can_professor_modify, get_classrooms, get_course_by_id, get_lesson_by_id, get_user_by_id, get_professor_by_course_id, \
    change_course_attr, add_lesson, get_lessons_by_course_id, delete_lesson, get_course_by_lesson_id,\
    confirm_attendance, change_lesson_information, get_lessons_bookable, get_full_lessons, book_lesson, delete_reservation, get_reservation_from_token, get_classrooms
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, DateField, SelectField, BooleanField, SubmitField, validators, SelectMultipleField, IntegerField, TextAreaField, TimeField
from wtforms.validators import DataRequired, ValidationError
import datetime

lessons = Blueprint("lessons_blueprint", __name__, template_folder = "templates")

def get_classrooms_tuple():
    list_classroom = get_classrooms()
    res = [("", "--Seleziona un tipo --")]
    for i in list_classroom:
        tuple = (i.ClassroomID, f'{i.Name} - Edificio {i.Building}')
        res.append(tuple)
    return res
        


class AddLesson(FlaskForm):
   
    # <--- ADD LESSON FORM ---> #
    date = DateField("Data", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data"})
    start_time = TimeField("Orario di Inizio", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Inizio"})
    end_time = TimeField("Orario di Fine", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Fine"})
    topic = TextAreaField("Argomento e Materiali", render_kw={"placeholder":"..."})
    type_lesson = SelectField('Modalità erogazione', choices=[("", "--Seleziona un tipo--"),("Frontale", "Frontale"),("Online", "Online"), ("Duale", "Duale")], validators=[DataRequired(message="Campo richiesto")])
    classroom = SelectField("Seleziona Aula", choices=get_classrooms_tuple())
    link = StringField("Link lezione")
    password = StringField("Password Lezione")

    submit_button = SubmitField()
    
    def validate_classroom(self, classroom):
        if self.type_lesson.data == 'Frontale' or self.type_lesson.data == "Duale":
            if classroom.data == "" or classroom is None or classroom.data is None:
                raise ValidationError("Aula obbligatoria in caso di lezione Frontale o Duale")

        elif self.type_lesson.data == 'Online':
            if classroom.data != "" and classroom is not None and classroom.data is not None:
                raise ValidationError("Non è richiesta l'aula per le lezione online")
    


class AddMultipleLessons(FlaskForm):
    start_date_2 = DateField("Data Inizio",validators =[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data Inizio"})
    end_date_2 = DateField("Data Fine",validators =[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data Fine"})
    start_time_2 = TimeField("Orario di Inizio", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Inizio"})
    end_time_2 = TimeField("Orario di Fine", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Orario di Fine"})
    classroom_2 = SelectField("Seleziona Aula", choices=get_classrooms_tuple())
    lesson_type_2 = SelectField('Modalità erogazione', choices=[("", "--Seleziona un tipo--"),("Frontale", "Frontale"),("Online", "Online"), ("Duale", "Duale")], validators=[DataRequired(message="Campo richiesto")])
    
    submit_lessons = SubmitField()

    def validate_classroom(self, classroom_2):
        if self.lesson_type_2 == "Frontale" or self.lesson_type_2 == 'Duale':
            if classroom_2.data == '' or classroom_2.data is None:
                raise ValidationError("Campo richiesto con modalità Duale/Frontale")

        elif self.lesson_type == 'Online':
            if classroom_2.data is not None or classroom_2 is not None or classroom_2.data != "":
                raise ValidationError("Non è richiesta aula per lezioni solo online")

    def validate_start_time_2(self, start_time_2):
        if start_time_2.data >= self.end_time_2.data:
            raise ValidationError("L'orario deve avere senso")
 

@lessons.route('/')
def lessons_home():
    pass


@lessons.route('/courses/<coursePage>/lessons', methods=['GET', 'POST'])
def lessons_course_home(coursePage):
    form = AddLesson()

    form2 = AddMultipleLessons()

    can_modify = can_professor_modify(current_user.get_id(), coursePage.upper())

    
    if form.submit_button.data and form.validate_on_submit() and can_modify:
        answer = add_lesson(form, coursePage.upper(), current_user.get_id())
        if answer == 'ClashError': #se l'inserimento non va a buon fine, avvertiamo il chiamante
            form.classroom.errors.append("Aula già prenotata per quell'ora")

        elif answer == 'DateError':
            form.start_time.errors.append("L'ora di inizio deve essere minore di quella di fine!")
            form.end_time.errors.append("L'ora di fine deve essere maggiore di quella di inzio")
        
        elif answer == "SameCourseClashError":
            form.start_time.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
            form.end_time.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
            form.date.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
        elif answer == "UnknownError":
            flash("Something goes wrong...")
        else:
            return redirect(url_for("lessons_blueprint.lessons_course_home", coursePage = coursePage))

    elif form2.submit_lessons.data and form2.validate_on_submit() and can_modify:
        
        add_multiple_lesson(form2, coursePage.upper(), current_user.get_id())


    list_lessons = get_lessons_by_course_id(coursePage.upper())

    
    return render_template("lessons.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user=current_user,
                            can_modify=can_modify,
                            form=form,
                            list_lessons = list_lessons,
                            course=get_course_by_id(coursePage.upper()),
                            form2 = form2
                        )


@lessons.route('/lessons/reservations')
def reservations():

    lessons_bookable = get_lessons_bookable(current_user.get_id())
    number_of_reservations = get_full_lessons()

    return render_template("reservations.html",
                            is_professor = False,
                            user=current_user,
                            subs_list = lessons_bookable,
                            lessons_seats_reserved = number_of_reservations
                            )



@lessons.route('/lessons/reservations/private')
def private():

    lessons_bookable = get_lessons_bookable(current_user.get_id())
    number_of_reservations = get_full_lessons()

    return render_template("reservations.html",
                            is_professor = False,
                            user=current_user,
                            subs_list = lessons_bookable,
                            lessons_seats_reserved = number_of_reservations

                            )


@lessons.route('/qr')
def qreader():
    return render_template("testqr.html", user=current_user, is_professor=False if not current_user.is_authenticated else current_user.hasRole("Professor"))

#crea  la relazione studente-lezioni per certificare che lo studente ha seguito la lezione x
#oppure se si tratta di una prenotazione di una frontallesson, esegue la prenotazione (a meno che i posti in aula non siano finiti)

@lessons.route("/action/lessons", methods=['POST'])
@login_required
def action_lesson():

    """
    All'interno di __init__.py è presente una procedura (della libreria di flask_wtf) che controlla il csrf token della richiesta di post
    questa pagina viene acceduta tramite richiesta ajax, dove da la viene passato il csrf_token generato dinamicamente quando la pagina viene loadata
    (Ad esempio dalla pagina delle lezioni di un corso, viene generato un csrf_token, ajax fa una richiesta di tipo POST a questa pagina ed inserisce
    come request headers il csrf token che viene generato.
    URL Inoltre cambia in base al tipo di richiesta che viene fatta sfruttando gli url arguments.
    Prima di eseguire la post, flask controllerà il csrf token, se è corretto procederà tutto nella norma, altrimenti verrà ritornato un errore 400)
    """


    action = request.args.get('action')
    lesson_id = int(request.args.get('lesson_id'))

    if action == 'delete':
        if can_professor_modify(current_user.get_id(), get_course_by_lesson_id(lesson_id).CourseID):
            if delete_lesson(lesson_id):
                return jsonify({'success' : True})
        return jsonify({'success': False})
    
    elif action == 'modify_topic':
        # topic = request.headers.get('topic')
        topic = request.form['topic']
        if can_professor_modify(current_user.get_id(), get_course_by_lesson_id(lesson_id).CourseID):
            if change_lesson_information(lesson_id, topic):
                return jsonify({'success' : True})

        return jsonify({'success' : False})

    elif action == 'reservation':
        # f = datetime.datetime.now()
        lesson = get_lesson_by_id(lesson_id)
        if lesson is None:
            return jsonify({"success" : False})

        list_lessons_bookable = get_lessons_bookable(current_user.get_id())
        
        for l in list_lessons_bookable:
            if lesson.LessonID == l.LessonID and l.StudentID == -1:
                if book_lesson(lesson_id, lesson.CourseID):
                    # print((datetime.datetime.now()-f).total_seconds())
                    return jsonify({"success" : True})
            
        return jsonify({"success" : False})

    elif action == 'delete_reservation':
        lesson = get_lesson_by_id(lesson_id)
        if lesson is None:
            return jsonify({"success" : False})

        if delete_reservation(lesson_id):
            return jsonify({"success" : True})

        return jsonify({"success" : False})

    elif action == 'formalize':
        if not current_user.hasRole("Admin"):
            abort(401)

        tok = request.args.get("token")
        reservation = get_reservation_from_token(tok)
        if reservations is not None:
            if reservation.HasValidation == False:
                bookable_lesson = get_lessons_bookable(reservation.StudentID)
                for lesson in bookable_lesson:
                    if lesson.LessonID == reservation.FrontalLessonID and lesson.StudentID >= 0:
                        confirm_attendance(reservation)
                        return jsonify({"success" : True})
        

        return jsonify({"success" : False})
            
        """
            in caso di lezione online lo studente dovrà inserire manualmente il token, che verrà mostrato dal prof.
            In caso di lezione frontale invece, lo studente dovrà presentare il qr code all'ingresso (al tablet) che verificherà se la prenotazione è valida
            Tipi di errore possibili:
                Se l'errore inizia con qr allora lo studente ha prenotato una lezione frontale e l'errore verrà mostrato dal tablet all'ingresso degli edifici
                Altrimenti se l'utente attuale è uno studente e sta inserendo manualmente il token per una lezione online, il possibile errore verrà mostrato 
                direttamente all'urente
        """
            
    return  jsonify({"success" : False})

"""

TRIGGER PER IMPEDIRE CHE UNO STUDENTE PRENOTI IN AULA CHE NON HANNO POSTI DISPONIBILI

CREATE TRIGGER check_reservation_classroom_seats
BEFORE INSERT ON Reservation
FRO EACH ROW EXECUTE FUNCTION func_check_reservation_classroom_seats()

CREATE FUNCTION func_check_reservation_classroom_seats() RETURN TRIGGER
BEGIN
    IF ( (SELECT COUNT(*)
        FROM Reservation r 
        WHERE NEW.FrontalLessonID = r.FrontalLessonID) >= (SELECT c.Seats
                                                           FROM Classroom c JOIN FrontalLesson fl USING(ClassroomID)
                                                           WHERE fl.LessonID = NEW.FrontalLessonID) ) THEN RAISE EXCEPTION 'SeatsNoMore';
    ENDIF;
    RETURN NEW                                                                                          
END

"""

"""

TRIGGER PER IMPEDIRE DI AGGIUNGERE UNA LEZIONE CHE HA GIÀ L'AULA OCCUPPATA IN QUELL'ORARIO/DATA

CREATE TRIGGER check_no_overlapping_lesson
BEFORE INSERT AND UPDATE ON FrontalLesson
FOR EACH ROW EXECUTE FUNCTION check_no_overlapping_lesson_func()

CREATE FUNCTION check_no_overlapping_lesson_func() RETURN TRIGGER
BEGIN
    IF (EXISTS (SELECT *
                FROM Lessons l NATURAL JOIN FrontalLesson fl
                WHERE (l.Date = NEW.Date) AND (fl.ClassroomID = NEW.ClassroomID) AND ((NEW.StartTime BETWEEN l.StartTime AND l.EndTime) 
                                                                                      OR (NEW.EndTime BETWEEN l.StartTime AND l.EndTime) 
                                                                                      OR (NEW.StartTime <= l.StartTime AND NEW.EndTime >= l.EndTime))) THEN RAISE "ClassroomNoASv"
                                                                                        
                )
    ENDIF;
    
    RETUNRN NEW
END

"""

"""
CREATE TRIGGER check_self_course_overlapping_lessons
BEFORE INSERT OR UPDATE ON Lessons
FOR EACH ROW EXECUTE FUNCTION check_self_course_overlapping_lessons_trigger()

CREATE FUNCTION check_self_course_overlapping_lessons_trigger() RETURNS TRIGGER
BEGIN
    IF EXISTS(SELECT *
              FROM Lessons l
              WHERE l.CourseID = NEW.CourseID AND l.Date = NEW.Date AND (NEW.StartTime BETWEEN l.StartTime AND l.EndTime
                                                                         OR NEW.EndTime BETWEEN l.StartTime AND l.EndTime
                                                                         OR NEW.StartTime <= l.StartTime AND NEW.EndTime >= l.EndTime)) THEN RAISE "SameCourseOverlapping"
    ENDIF;
    RETURN NEW
END

"""