from flask import Blueprint, jsonify, render_template, url_for, redirect, flash, abort, request, logging, session as flasksession
from flask_login import current_user, login_required
from DaisPCTO.auth import role_required
from DaisPCTO.db import add_multiple_lesson, can_professor_modify, exists_role_user, formalize_student, get_classrooms, get_course_by_id, get_lesson_by_id, get_students_by_course, get_user_by_id, get_professor_by_course_id, \
    change_course_attr, add_lesson, get_lessons_by_course_id, delete_lesson, get_course_by_lesson_id,\
    confirm_attendance, change_lesson_information, get_lessons_bookable, get_full_lessons, book_lesson, delete_reservation,\
    get_reservation_from_token, get_classrooms, formalize_student, get_lesson_from_token, get_users_role, is_subscribed, update_lesson
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
 

class UpdateLesson(FlaskForm):
    date_update = DateField("Data lezione", validators =[DataRequired(message="Campo richiesto")], render_kw={"placeholder" : "Data"})
    start_time_update = TimeField("Orario di inizio", validators =[DataRequired(message="Campo richiesto")], render_kw={"placeholder" : "Orario di Inizio"})
    end_time_update = TimeField("Orario di fine", validators =[DataRequired(message="Campo richiesto")], render_kw={"placeholder" : "Orario di Fine"})
    classroom_update = SelectField("Seleziona aula", choices=get_classrooms_tuple())
    lesson_type_update = SelectField('Modalità erogazione', choices=[("", "--Seleziona un tipo--"),("Frontale", "Frontale"),("Online", "Online"), ("Duale", "Duale")], validators=[DataRequired(message="Campo richiesto")])
    link_update = StringField("Link lezione", render_kw={"placeholder" : "Link lezione"})
    password_update = StringField("Password lezione", render_kw={"placeholder" : "Password lezione"})

    lesson_id = IntegerField()
    
    submit_update = SubmitField()


    def validate_classroom_update(self, classroom_update):
        if self.lesson_type_update.data == 'Frontale' or self.lesson_type_update.data == "Duale":
            if classroom_update.data == "" or classroom_update is None or classroom_update.data is None:
                raise ValidationError("Aula obbligatoria in caso di lezione Frontale o Duale")

        elif self.lesson_type_update.data == 'Online':
            if classroom_update.data != "" and classroom_update is not None and classroom_update.data is not None:
                raise ValidationError("Non è richiesta l'aula per le lezione online")
"""
Pagina di home contenente una lista con tutte le lezioni passate e future relative ad un corso, se l'utente corrente si tratta di uno studente la visualizzazione
della pagina corrisponderà ad una normalissima lettura, in caso di professore associato a quel corso invece, avrà a disposizione una serie di pulsanti atti
a modificare, aggiungere ed eliminare lezioni.
Il successo o l'insuccesso di relative modifiche alle lezioni avverrà tramite il try->catch dal file db.py ritornando gli
gli errori sottoforma di stringa, ed in base all'errore ritorniamo un messaggio d'errore diverso al chiamante.
Tutti gli errori interessati sono lanciati da Postgresql dopo l'eventuale avvenuta esecuzione di un trigger
"""
@lessons.route('/courses/<coursePage>/lessons', methods=['GET', 'POST'])
def lessons_course_home(coursePage):
    form = AddLesson()

    form2 = AddMultipleLessons()

    form3 = UpdateLesson()
   
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

    elif form3.submit_update.data and form3.validate_on_submit() and can_modify:
        answer = update_lesson(form3.lesson_id.data, form3)
        
        if answer == 'ClashError':
            form3.classroom_update.errors.append("Aula già prenotata per quell'ora")

        elif answer == 'DateError':
            form3.start_time_update.errors.append("L'ora di inizio deve essere minore di quella di fine!")
            form3.end_time.errors_update.append("L'ora di fine deve essere maggiore di quella di inzio")
        
        elif answer == "SameCourseClashError":
            form3.start_time_update.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
            form3.end_time_update.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
            form3.date_update.errors.append("Un'altra tua lezione è presente nel range di orario selezionato")
        elif answer == "UnknownError":
            flash("Something goes wrong...")
        else:
            return redirect(url_for("lessons_blueprint.lessons_course_home", coursePage = coursePage))

    list_lessons = get_lessons_by_course_id(coursePage.upper())

    return render_template("lessons.html",
                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                            user=current_user,
                            can_modify=can_modify,
                            form=form,
                            list_lessons = list_lessons,
                            course=get_course_by_id(coursePage.upper()),
                            form2 = form2,
                            form3 = form3,
                            roles = get_users_role(current_user.get_id())
                        )

"""
Pagina per prenotare le lezioni frontali per uno studente
"""
@lessons.route('/lessons/reservations')
@role_required("Student")
def reservations():

    lessons_bookable = get_lessons_bookable(current_user.get_id())
    number_of_reservations = get_full_lessons()

    return render_template("reservations.html",
                            is_professor = False,
                            user=current_user,
                            subs_list = lessons_bookable,
                            lessons_seats_reserved = number_of_reservations,
                            roles = get_users_role(current_user.get_id())
                            )



"""
Lista di tutte le prenotazioni già effettuate di uno studente
"""
@lessons.route('/lessons/reservations/private')
@login_required
def private():

    lessons_bookable = get_lessons_bookable(current_user.get_id())
    number_of_reservations = get_full_lessons()

    return render_template("reservations.html",
                            is_professor = False,
                            user=current_user,
                            subs_list = lessons_bookable,
                            lessons_seats_reserved = number_of_reservations,
                            roles = get_users_role(current_user.get_id())
                        )

"""
La pagina qr_scanner ha due versioni: 
    Studente:
        Lo studente può scannerizzare QR che vengono forniti dal professore (relativi ad una lezione), 
        e se valido viene creata l'associazione studente-lezione, incrementando così le ore seguite del corso di suddetto studente
    QrReader:
        Il QrReader funziona in simil-modo ai tablet piazzati all'entrata di ogni edificio al campus scientifico, lo studente dovrà presentare
        un qrcode di prenotazione in aula al tablet, e se valido lo scanner lancierà un messaggio di avvenuto successo, dopodiché, come prima, verrà
        creata una relazione studente-lezione, incrementando così le ore seguite del corso di suddetto studente
"""
@lessons.route('/qr')
@login_required
def qreader():
    is_reader_qr = exists_role_user(current_user.get_id(), "QrReader")

    return render_template("qr_scanner.html", is_reader = is_reader_qr, 
                                          user=current_user, 
                                          is_professor=False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                                          roles = get_users_role(current_user.get_id()))

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

    """
    Action lesson è una route abbastanza grande che prende argomenti ed in base al tipo dell'azione assumerà un comportamento diverso.
    Questa è una route che viene richiamata da una procedura ajax, infatti la sua risposta avviene attraverso un json, il successo o meno dell'azione avviene
    attraverso il campo "success" del dizionario che può essere true o false, tutte le altre chiavi del dizionario sono dati utili al chiamante per modificare
    in modo dinamico la pagina web
    """

    action = request.args.get('action') #id utente che sta compiendo l'azione
    lesson_id = int(request.args.get('lesson_id')) #lezione target

    
    if action == 'delete':
        """In caso di action delete per prima cosa si controlla che l'utente corrente è un professore, e se tale professore può modificare la pagina del corso,
        in caso affermativo la lezione target verrà eliminata"""
        if can_professor_modify(current_user.get_id(), get_course_by_lesson_id(lesson_id).CourseID):
            if delete_lesson(lesson_id):
                return jsonify({'success' : True})
        return jsonify({'success': False})
    
    elif action == 'modify_topic':
        """In questo caso l'azione richiesta è una modifica del topic della lezione target, anche qua viene controllato il professore e se tutto procede nel verso giusto
        il topic della lezione verrà cambiato correttamente"""
        topic = request.form['topic']
        if can_professor_modify(current_user.get_id(), get_course_by_lesson_id(lesson_id).CourseID):
            if change_lesson_information(lesson_id, topic):
                return jsonify({'success' : True})

        return jsonify({'success' : False})

    elif action == 'reservation':
        """
        Azione compiuta da uno studente al fine di prenotare un posto in aula, la capienza dell'aula viene controllata tramite trigger, il dbms lancerà un messaggio
        'SeatsNoMore' in caso di posti non disponibili, e la funzione 'book_lesson' ritornerà False.
        """

        lesson = get_lesson_by_id(lesson_id)
        if lesson is None:
            return jsonify({"success" : False})

        list_lessons_bookable = get_lessons_bookable(current_user.get_id())
        
        for l in list_lessons_bookable:
            #lesson.StudentID == -1 significa che quello studente NON ha ancora prenotato quella lezione
            if lesson.LessonID == l.LessonID and l.StudentID == -1:
                if book_lesson(lesson_id, lesson.CourseID):
                    return jsonify({"success" : True})
            
        return jsonify({"success" : False})

    elif action == 'delete_reservation':
        """
        Altra azione compiuta da studenti per annullare una prenotazione in aula, tuttavia nel caso suddetto studente ha già confermato la propria presenza in aula
        usando quella prenotazione, non sarà più possibile annularla
        """
        lesson = get_lesson_by_id(lesson_id)
        if lesson is None:
            return jsonify({"success" : False})

        if delete_reservation(lesson_id):
            return jsonify({"success" : True})

        return jsonify({"success" : False})

    elif action == 'formalize':
        """
        Azione compiuta dal "Tablet all'entrata dell'edificio" o da un utente con ruolo di qr-code, ajax manda un token che ha convertito da un qrcode
        Si accede alla tabella reservation e si cerca suddetto token e si controlla se è una prenotazione valida, (quindi se il giorno della lezione della prenotazione
        è oggi, e se l'ore di inizio della lezione è fra al massimo due ore rispetto ad ora), inoltre viene anche controllato il campo "HasValidation" che verrà
        automaticamente settato a true la prima volta che si scannerizza il codice.

        Dal token di conseguenza sarà facile ottenere la riga della tabella contenente id studente e id lezione di riferimento, quindi si potrà creare una relazione
        lezione-studente.
        """
        if not exists_role_user(current_user.get_id(), "QrReader"):
            abort(401)

        tok = request.args.get("token")
        reservation = get_reservation_from_token(tok)
 
        if reservation is not None:    
            if reservation.HasValidation == False:
                bookable_lesson = get_lessons_bookable(reservation.StudentID)
                for lesson in bookable_lesson:                  
                    '''
                        se il current user è un qrreader significa che chi sta facendo la richiesta è il tablet che sta davanti all'ingresso, quindi stiamo formalizzando una prenotazione frontale
                        la logica sarebbe che uno studente può prenotarsi al massimo due ore prima rispetto all'inizio della lezione ed nel giorno stesso
                    '''
                    if lesson.LessonID == reservation.FrontalLessonID and lesson.StudentID >= 0 and lesson.Date == datetime.datetime.today().date():
                        date_1 = datetime.datetime.combine(datetime.datetime.today().date(), lesson.StartTime) - datetime.datetime.today()
                        if date_1.total_seconds()/3600 <= 2 and date_1.total_seconds()/3600 >= 0:
                            confirm_attendance(reservation)
                            return jsonify({"success" : True})
                    
        
        return jsonify({"success" : False})
        
    elif action == 'formalize-student':

        '''
        a differenza della formalize fatta sopra, in questo caso sono gli studenti che scanerizzano un qr code mostrato dal prof, per certificare la loro presenza
        azione pensata più per gli studenti online che ovviamente non si possono prenotare, tuttavia anche quelli in presenza possono farlo, nel caso non si siano potuti prenotare per tempo
        o per mancata scanerizzazione qrcode della loro prenotazione a causa di mal funzionamenti del tablet all'ingresso o quant'altro
        '''

        """
        Azione che ha come conseguenza la stessa cosa di quella precedente, ma viene effettuata da uno studente. In questo caso il professore mostrerà alla classe
        un qr code che essi dovrano scannerizzare con il loro telefoni, verrà chiamata una procedura ajax che richiamerà questa route, dal token che si prende nei parametri
        url si risale alla lezione, e dopo una serie di controlli verrà creata la relazione studente-lezione:
            - L'ora corrente deve essere compresa fra l'ora di inizio e l'ora di fine della lezione target
            - Data corrente uguale alla data della lezione target
            - Nessun vincolo per tipo di lezione (anche gli studenti in presenza potranno scannerizzare il qrcode, decisione presa in caso di eventuali guasti del tablet all'entrata o altri problemi ignoti)
            - Lo studente deve effettivamente essere iscritto al corso
        """
        if not exists_role_user(current_user.get_id(), "Student"):
            abort(401)

        token = request.args.get("token")
        
        lesson = get_lesson_from_token(token)

        # students = get_students_by_course(lesson.CourseID)
        is_subbed = is_subscribed(current_user.get_id(), lesson.CourseID)
        
        # for s in students:
        #     if s.UserID == current_user.get_id():
        if is_subbed:
            if lesson.Date == datetime.datetime.today().date():
                if lesson.EndTime >= datetime.datetime.today().time() and lesson.StartTime <= datetime.datetime.today().time():
                    formalize_student(current_user.get_id(), lesson.LessonID)
                    flash("Presenza confermata con successo")
                    return jsonify({"success" : True})
       
        return jsonify({"success" : False})
            
    return  jsonify({"success" : False})