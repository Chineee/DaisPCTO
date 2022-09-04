from DaisPCTO.models import Certificate, Feedback,\
     ProfessorCourse, StudentCourse, User, Student, Professor,\
     UserRole, Course, Role, Lesson, StudentLesson, Reservation, \
     FrontalLesson, OnlineLesson, Classroom, School, QnA
from sqlalchemy import create_engine, and_, not_, or_, not_, exc, func, case, text
from sqlalchemy.orm import sessionmaker
from flask_login import current_user
from flask import flash, session as flasksession
from flask_bcrypt import generate_password_hash, check_password_hash
import random 
import datetime 
import json

engine = {
    "Admin" : create_engine("postgresql://postgres:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0),
    "Student" : create_engine("postgresql://Student:studente01@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Professor" : create_engine("postgresql://Professor:123456@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Anonymous" : create_engine("postgresql://Anonymous:12345678@localhost/testone8", echo=False, pool_size=20, max_overflow=0),
    "QrReader" : create_engine("postgresql://QrReader:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0),
}

Session = sessionmaker()

"""
Ogni volta che inizia una transazione viene fatta una connessione con il database in base al ruolo dell'utente corrente.
Il ruolo viene controllato avendo l'id del current_user, e guardando dentro la relativa tabella UserRole.
Nel DBMS sono definiti i ruoli con permessi diversi per avere una maggiore sicurezza.
"""

def get_engine(flask_request = False):
    
    if flask_request: #la flask_request viene settata a true solo quando viene chiamata la get_user_by_id attraverso la load user, ovvero quando l'utente deve ancora essere
        #caricato
        return engine['Anonymous']

    if current_user == None:
        return engine['Anonymous']
    if not current_user.is_authenticated:
        return engine['Anonymous']
    if exists_role_user(current_user.get_id(), "Student"):
        return engine['Student']
    if exists_role_user(current_user.get_id(), "Professor"):
        return engine['Professor']
    if exists_role_user(current_user.get_id(), "Admin"):
        return engine['Admin']
    if exists_role_user(current_user.get_id(), "QrReader"):
        return engine['QrReader']

    return None

def get_users_role(user_id):
    try:
        session = Session(bind=engine['Admin'])
        roles = session.query(Role)\
            .join(UserRole, UserRole.RoleID == Role.RoleID)\
            .filter(UserRole.UserID == user_id)\
            .all()
    except exc.SQLAlchemyError as e:
        session.close()
        return []
    
    roles = [r.Name for r in roles]
 
    return roles
    
def exists_role_user(user_id, role):
    try:
        session = Session(bind=engine['Admin'])
        q = session.query(UserRole).join(Role).filter(and_(UserRole.UserID == user_id, Role.Name == role)).first() is not None
    except Exception as e:
        session.close()
        q = False
    finally:
        session.close()
    return q

def get_course_by_id(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Course).filter(Course.CourseID == course_id).first()
    except:
        return None

"""Ritorniamo un oggetto student dato il suo ID"""
def get_student_by_user(user_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Student).filter(Student.UserID == user_id).first()
    except:
        session.close()
        session.rollback()
        return None

"""Ritorniamo un oggetto di tipo User dato il suo id, flask_request è settato a true quando la funzione che la richiama viene dalla load_user della libreria di flask_login"""
def get_user_by_id(id, flask_request=False):
    try:
        session = Session(bind=get_engine(flask_request))
    # session.connection(execution_options={'isolation_level': 'SERIALIZABLE', "postgresql_readonly" : True})
    # try:
    #     session.add(User(UserID=10))
    # except:
    #     session.rollback()
    #     print("roll back")
    # print("OK")
        return session.query(User).filter(User.UserID == id).first()
    except Exception as e:
        return None

"""Ritorniamo un oggetto di tipo User dato la sua mail"""
def get_user_by_email(email):
    try:
        session = Session(bind=get_engine())
        return session.query(User).filter(User.email == email).first()
    except Exception as e:
        print(e)
        return None

"""
Viene passato un oggetto di tipo form contenente tutti i campi per creare uno user, se la richiesta viene dalla register viene creato uno studente, altrimenti
viene creato un professore
"""
def create_user(form, password = None, is_student=True):

    Name = form.name.data
    Surname = form.surname.data
    Email = form.email.data
    if is_student:
        Password = form.password.data
        Gender = form.gender.data
        Phone = form.phone.data
    else:
        Password = password
        Gender = None 
        Phone = None

    new_user = User(Name=Name, Surname=Surname, Gender=Gender, email=Email, Password = generate_password_hash(Password).decode('utf-8'), PhoneNumber=Phone)
    
    return new_user

"""
Viene aggiunto un utente al database.
Il codice di errore 23505 è definito da psycopg2 ed indica che stiamo che stiamo inserendo una riga con un attribute che ha come vincolo Unique già esistente
Nella tabella User l'attributo con vincolo Unique è la mail, di conseguenza entra in errore se proviamo ad inserire un utente con una mail già registrata.
Nel caso questo dovesse accadere, verrà visualizzato un messaggio di errore nel form di registrazione.
Se l'inserimento nella tabella va a buon fine si provvederà ad inserire l'utente anche nella tabella di studente o professore a seconda di chi sta facendo la richiesta.
"""
def add_user(user, form,  is_student=True):
    try:
        session = Session(bind=get_engine())
        session.add(user)
        session.commit()
        if is_student:
            add_student(user, form)
        else:
            add_professor(user)
    except exc.SQLAlchemyError as e:
        print(e)
        session.rollback()
        if e.orig.pgcode == '23505': 
            return "UniqueError"
        return False 
    return True

"""Viene aggiunto un professore al database"""
def add_professor(user):
    try:
        session = Session(bind=get_engine())
        session.add_all([Professor(UserID=user.UserID), UserRole(UserID=user.UserID, RoleID=3)])
        session.commit()
    except:
        session.rollback()
        session.close()

"""Viene aggiunto uno studente al database"""
def add_student(user, form):

    #MODIFICARE ADD STUDENT IN MODO CHE ADDI TUTTI GLI ALTRI CAMPI
    school_id = form.school_id.data
    student_city = form.student_city.data.partition(',')[0]
    student_birth_date = form.birth_date.data
    student_school_year = form.school_year.data
    student_address = form.address.data

    try:
        session = Session(bind=get_engine())
        session.add_all([Student(UserID = user.UserID, \
                                SchoolID=school_id, \
                                birthDate = student_birth_date, \
                                Address=student_address, \
                                SchoolYear = student_school_year,\
                                City = student_city
                                ), \
            UserRole(UserID = user.UserID, \
                    RoleID = 2)])
        session.commit()
    except Exception as e:
        session.rollback()

"""
Confronto di password in fase di login per gli utenti non autenticati e per gli utenti autenticati che hanno intenzione di cambiare la propria password
"""
def compare_password(db_password, inserted_password):
    return check_password_hash(db_password, inserted_password)      

"""
Alla creazione di un corso viene aggiunta la relativa riga nella tabella associative ProfessorCourse, con il prof che ha creato il corso ed il corso stesso.
Il professore ha inoltre la possibilità di aggiungere collaboratori al corso.
"""
def add_professor_course(course_id, prof_id):
    try:
        session = Session(bind=get_engine())
        session.add(ProfessorCourse(CourseID=course_id, ProfessorID=prof_id))
        session.commit()
    except exc.SQLAlchemyError as e:
        session.rollback()

"""
Funzione per aggiungere un corso dato un oggetto di tipo FlaskForm
""" 
def add_course(form):
    
    name = form.name.data
    course_id = form.course_id.data.upper()
    description = form.description.data 
    max_students = form.max_students.data
    min_hours = form.min_hour_certificate.data
    
    try:
        session = Session(bind=get_engine())
        session.add(Course(OpenFeedback=False, CourseID=course_id, Name=name, Description = description, MaxStudents=max_students, MinHourCertificate = min_hours))
        session.commit()
        add_professor_course(course_id, current_user.get_id())
    except exc.SQLAlchemyError as e:
        print(e)
        session.rollback()
        
"""
ritorna true se e solo se esiste una tupla che contenga l'id del professore e l'id del corso all'interno della tabella professorcourse,
se questo risulta essere vero allora esiste una relazione fra professore e corso e quindi l'utente messo in input ha accesso al corso.
"""
def can_professor_modify(prof_id, course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(ProfessorCourse).filter(and_(ProfessorCourse.ProfessorID == prof_id, ProfessorCourse.CourseID == course_id)).first() is not None
    except Exception as e:
        print(e)
        return False
"""Ritorna una lista contenente oggetti di tipo User che sono professori e che possono accedere al corso"""
def get_professor_by_course_id(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(User).filter(and_(ProfessorCourse.CourseID == course_id, ProfessorCourse.ProfessorID == User.UserID)).all()
    except:
        session.close()
        return None

"""Conta quanti studenti sono iscritti ad un corso"""
def count_student(course_id):
    try:
        session = Session(bind=get_engine())

        return session.query(StudentCourse).filter(StudentCourse.CourseID == course_id).count()
    except:
        return None

"""
Funzione di update per modificare dati del corso in questione (Solo professori che hanno accesso al corso possono farlo, controlli che vengono effettuati prima
di chiamare la funzione, in ogni caso se nel caso peggiore l'utente non dovesse essere un professore, il DBMS ritornerà un errore perché solo Professori possono fare 
update sulla tabelle Courses)
"""
def change_course_attr(form, course_id):
    try:
        session = Session(bind=get_engine())
        
        course = session.query(Course).filter(Course.CourseID == course_id)

        if form.name.data is not None:
            course.update({Course.Name : form.name.data})
        if form.description.data is not None:
            course.update({Course.Description : form.description.data})
        if form.max_students.data is not None:
            course.update({Course.MaxStudents : form.max_students.data})
        if form.min_hour_certificate is not None:
            course.update({Course.MinHourCertificate : form.min_hour_certificate.data})

        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

"""
Funzione per aprire o chiudere i feedback di un corso
"""
def change_feedback(course_id):
    try: 
        session = Session(bind=get_engine())       
        session.query(Course).filter(Course.CourseID == course_id).update({Course.OpenFeedback : not_(Course.OpenFeedback)})
        session.commit()

        return session.query(Course).filter(Course.CourseID == course_id).first().OpenFeedback
            
    except:
        session.rollback()
    finally:
        session.close()

"""
Funzione per studenti per iscriversi ad un corso
"""
def subscribe_course(student_id, course_id):
    try:
        session = Session(bind=get_engine())
        session.add(StudentCourse(StudentID=student_id, CourseID=course_id, HasSentFeedback = False))
        session.commit()
    except:
        session.rollback()

"""
Funzione per controllare se uno studente è iscritto ad un cortso
"""
def is_subscribed(student_id, course_id):
    try:
        session = Session(bind=get_engine())
        
        if session.query(StudentCourse).filter(and_(StudentCourse.StudentID == student_id, StudentCourse.CourseID == course_id)).first() is None:
            return False
        return True
    except:
        return False

"""
Funzione per studenti per disiscriversi da un corso
"""
def delete_subscription(student_id, course_id): 
    try:
        session = Session(bind=get_engine())      

        session.query(StudentCourse).filter(and_(StudentCourse.StudentID == student_id, StudentCourse.CourseID == course_id)).delete()
        session.commit()
    except:
        session.rollback()

"""
Funzione per i professori per aggiungere una nuova lezione, il token viene generato secondo i dati scritti sotto, e saremo sempre certi che sarà univoco,
dato che non potrà MAI esserci una lezione nella stessa data, stessa ora di inizio e stessa ora di fine e stesso ID del corso. Inoltre due lezioni diverse
non potranno alloggiare nella medesima aula nello stesso range di orario
"""
def add_lesson(form, course_id, professor):
    date = form.date.data
    start_time = form.start_time.data
    end_time = form.end_time.data
    topic = form.topic.data
    type_lesson = form.type_lesson.data
    is_dual = True if type_lesson == "Duale" else False
    classroom = form.classroom.data
    link = form.link.data
    password = form.password.data
    token = generate_password_hash(f'{current_user.get_id()}{course_id}{date}{start_time}{end_time}{classroom}{random.randint(0, 10000)}').decode('utf-8')
    lesson_new = Lesson(Date = date, StartTime = start_time, EndTime = end_time, Topic = topic, IsDual = is_dual, CourseID = course_id, ProfessorID=professor, Token=token)

    return _add_lesson(lesson_new, type_lesson, classroom, link, password)

"""
Funzione di supporto per aggiungere una lezione al database, il DBMS ritornerà errori differenti a seconda dei casi. "ClashError" indica due lezioni nella stessa aula
nello stesso range di orario.
"SameCourseOverlapping" indica che ci sono due lezioni dello stesso corso nellol stesso range di orario, che esse siano online, frontali o duali non ha importanza.
Il codice di errore 23514 di psycopg2 invece indica che stiamo violando un checkconstraint, nella tabella lesson il check impone che StartTime sia strettamente minore di EndTime
"""
def _add_lesson(lesson_new, type_less, classroom, link=None, password=None):
    try: 
        session = Session(bind=get_engine())
        session.add(lesson_new)
        session.flush()

        if (type_less == "Frontale"):
            session.add(FrontalLesson(LessonID = lesson_new.LessonID , ClassroomID = classroom))

        elif (type_less == "Online"):
            session.add(OnlineLesson(LessonID=lesson_new.LessonID, RoomLink = link, RoomPassword = password))

        elif (type_less == "Duale"):
            session.add(FrontalLesson(LessonID = lesson_new.LessonID , ClassroomID = classroom))
            session.add(OnlineLesson(LessonID=lesson_new.LessonID, RoomLink = link, RoomPassword = password))
        session.commit()
    except exc.SQLAlchemyError as e:
        session.rollback()
        
        if e.orig.diag.message_primary == "LessonOverlapping":
            # delete_lesson(lesson_new.LessonID)
            return "ClashError"

        if e.orig.diag.message_primary == "SameCourseOverlapping":
            return "SameCourseClashError"

        if int(e.orig.pgcode) == 23514: #il code 23514 indica un check error che ritorna il dbms
            return "DataError"
        
        return "UnknownError"
    finally:
        session.close()
    return "Success"

"""
Sempre una funzione per i professori ma aggiunge più lezioni insieme, dati richiesti:
Data inizio A, Data fine B, Orario e tipo di lezioni:
A quel punto verranno aggiunte tutte le lezioni settimanalmente che vanno dal giorno A compreso al giorno B compreso (se possibile, altrimenti eslcuso).
Il sistema aggiungerà tutte le lezioni possibile, se ci dovesse essere un overlapping, escluderà SOLO quelle che danno errore, e non tutte quante.
"""
def add_multiple_lesson(form, course_id, professor):
    """
    VOGLIAMO FARE IN MODO CHE AGGIUNGA TUTTE LE LEZIONI CHE SI POSSONO AGGIUNGERE, IGNORANDO QUELLE CHE NON SI POSSONO AGGIUNGERE
    """
    start_date = form.start_date_2.data
    end_date = form.end_date_2.data
    diff_date = start_date
    
    is_dual = True if form.lesson_type_2.data == "Duale" else False

    while diff_date < end_date:
        token = generate_password_hash(f'{current_user.get_id()}{course_id}{diff_date}{form.start_time_2.data}{form.end_time_2.data}{form.classroom_2.data}{random.randint(0, 1000)}').decode('utf-8')
        lesson_new = Lesson(Date = diff_date, StartTime = form.start_time_2.data, EndTime = form.end_time_2.data, CourseID = course_id, IsDual = is_dual, ProfessorID=professor, Token=token)

        result_query = _add_lesson(lesson_new, form.lesson_type_2.data, form.classroom_2.data)
       
        if result_query == 'ClashError' or result_query == "SameCourseClashError":
            flash(f'Lezione del {diff_date} non aggiunta per sovrapposizione')
    
        diff_date = diff_date + datetime.timedelta(days=7)

"""
Funzione per i professori per eliminare una lezione
"""
def delete_lesson(lesson_id):
    try:
        session = Session(bind=get_engine())
        session.query(Lesson).filter(Lesson.LessonID == lesson_id).delete()
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
        return False 
    return True

"""
Ritorna una lista contenente tutte le lezioni di un corso, con le relative aula (se si tratta di lezioni frontali o duali) ed i relativi link di accesso
(se si tratta di lezioni online o duali) e tutte le altre informazioni necessarie agli studenti come: Data e Orario.
il parametro isouter=True indica una LEFT OUTER JOIN al fine di facilitare l'ottenimento di TUTTE le informazioni di una lezione (se esistenti,
altrimenti verranno settate a Null)
facendo una singola query
"""
def get_lessons_by_course_id(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Lesson.LessonID, Lesson.CourseID, Lesson.Date, Lesson.StartTime, Lesson.EndTime, Lesson.Topic, Classroom.Name, Classroom.Building, Lesson.IsDual, OnlineLesson.RoomLink, OnlineLesson.RoomPassword, Lesson.Token)\
            .join(FrontalLesson, Lesson.LessonID == FrontalLesson.LessonID, isouter = True)\
            .join(Classroom, Classroom.ClassroomID == FrontalLesson.ClassroomID, isouter=True)\
            .join(OnlineLesson, OnlineLesson.LessonID == Lesson.LessonID, isouter = True)\
            .filter(Lesson.CourseID == course_id)\
            .order_by(Lesson.Date, Lesson.StartTime).all()
    except Exception as e:
        print(e)
        return None

"""
Funzione che ritorna un oggetto di tipo Course data una sua lezione
"""
def get_course_by_lesson_id(lesson_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Course).filter(and_(Lesson.LessonID == lesson_id, Course.CourseID == Lesson.CourseID)).first()
    except:
        return None

"""
Funzione per i professori per modificare il topic di una lezione, nel nostro caso il topic della lezione corrisponderà anche a link e materiali utili per gli studenti
"""    
def change_lesson_information(lesson_id, data):
    try:
        session = Session(bind=get_engine()) 
        session.query(Lesson).filter(Lesson.LessonID == lesson_id).update({Lesson.Topic : data})
        session.commit()
    except:
        session.rollback()
        return False 
    return True

"""
Ritorna una lista contenente tutti i corsi disponibili
"""
def get_courses_list():
    try:
        session = Session(bind=get_engine())
        return session.query(Course).order_by(Course.Name).all()
    except Exception as e:
        print(e)
        return []

"""
Ritorna una lista di tutti i professori appartenenti alla tabella ProfessorsCourses
"""
def get_professor_courses(user_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Course)\
            .join(ProfessorCourse)\
            .filter(ProfessorCourse.ProfessorID == user_id)\
            .order_by(Course.Name)\
            .all()
    except:
        return None

"""
Ritorna una lista di tutti gli studenti iscritti a dei corsi, con le relative informazioni principali, tra cui quante ore di lezioni hanno seguito per ogni corso
"""
def get_student_courses(user_id):
    try:
        session = Session(bind=get_engine())
        
        query = session.query(Course.CourseID, Course.Name, Course.Description, Course.MinHourCertificate, func.sum(case((and_(Lesson.StartTime.isnot(None), Lesson.EndTime.isnot(None)), Lesson.EndTime-Lesson.StartTime), else_="00:00:00")).label("Hours")) \
                    .join(StudentCourse, StudentCourse.CourseID == Course.CourseID)\
                    .join(StudentLesson, StudentLesson.StudentID == StudentCourse.StudentID, isouter=True)\
                    .join(Lesson, and_(Lesson.LessonID == StudentLesson.LessonID, Lesson.CourseID == Course.CourseID), isouter=True)\
                    .filter(StudentCourse.StudentID == user_id)\
                    .order_by(Course.Name)\
                    .group_by(Course.CourseID, Course.Name, Course.Description, Course.MinHourCertificate).all()

        return query
    except Exception as e:
        print(e)
        return None

"""
Ritorna una lista di tutti gli studenti iscritti ad un corso specifico
"""
def get_students_by_course(course_id):
    try:
        session = Session(bind=get_engine())

        return session.query(User.Name, User.Surname, Student.birthDate, Student.City, User.UserID).join(Student, Student.UserID == User.UserID)\
            .filter(and_(StudentCourse.CourseID == course_id, StudentCourse.StudentID == Student.UserID))\
            .order_by(User.Surname, User.Name)\
            .all()
    except Exception as e:
        print(e)
        return []

"""
Ritorna un oggetto di tipo lesson dato il suo ID
"""
def get_lesson_by_id(lesson_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Lesson).filter(Lesson.LessonID == lesson_id).first()
    except:
        return None

"""
Ritorna una lista contenente oggetti di tipo Lesson, che hanno la caratteristica di essere disponibile alla prenotazione (per lezioni frontali).
In particolare ritorna una lista di lezioni frontali con le relative informazioni, che hanno le seguenti caratteristiche:
    Se la data è uguale alla data corrente, allora Lesson.StartTime deve essere maggiore dell'ore corrente.
    Altrimenti la data della lezione deve essere al massimo fra 6 giorni rispetto alla data corrente
"""
def get_lessons_bookable(user_id):
    try:
        
        session = Session(bind=get_engine())

        return session.query(Course.Name.label("CourseName"), Lesson.Date, Lesson.StartTime, Lesson.EndTime, Classroom.Name, Classroom.Building, Classroom.Seats, Lesson.LessonID, func.coalesce(Reservation.StudentID, -1).label("StudentID"), Reservation.ReservationID)\
            .join(Course, Course.CourseID == Lesson.CourseID)\
            .join(StudentCourse, and_(StudentCourse.StudentID == user_id, StudentCourse.CourseID == Course.CourseID))\
            .join(FrontalLesson, FrontalLesson.LessonID == Lesson.LessonID)\
            .join(Classroom, Classroom.ClassroomID == FrontalLesson.ClassroomID)\
            .join(Reservation, and_(Reservation.FrontalLessonID == FrontalLesson.LessonID, Reservation.StudentID == user_id), isouter=True)\
            .filter(or_(
                    and_(Lesson.Date - func.current_date() <='7', Lesson.Date - func.current_date() > '0'),
                    and_(Lesson.StartTime > func.current_time(), Lesson.Date - func.current_date() == '0')
                    ))\
            .order_by(Lesson.Date, Lesson.StartTime, Course.Name)\
            .all()            

    except exc.SQLAlchemyError as e:
        return None

"""
Ritorna il numero di posti prenotati per ogni lezione frontale
"""
def get_full_lessons():
    try:
        session = Session(bind=get_engine())
        return session.query(FrontalLesson.LessonID, func.count(Reservation.StudentID).label("Reserv"), Classroom.Seats)\
            .join(Classroom, Classroom.ClassroomID == FrontalLesson.ClassroomID)\
            .join(Reservation, Reservation.FrontalLessonID == FrontalLesson.LessonID, isouter=True)\
            .group_by(FrontalLesson.LessonID, Classroom.Seats)\
            .all()

    except Exception as e:
        print(e)
        return []

"""
Funzione per gli studenti per prenotare un posto ad una lezione frontale, il token che viene generato funziona in simil modo al token generato per le lezioni
L'errore che ritorna il DBMS "SeatsNoMore" indica che non ci sono più posti a sedere e quindi la prenotazione fallisce
"""
def book_lesson(frontalLesson_id, course_id):
    try:
        session = Session(bind=get_engine())
        token = generate_password_hash(f'{current_user.get_id()}{frontalLesson_id}{course_id}{datetime.datetime.now()}', 10).decode('utf-8')
        session.add(Reservation(StudentID = current_user.get_id(), FrontalLessonID = frontalLesson_id, HasValidation = False, ReservationID = token))
        session.commit()
        
    except exc.SQLAlchemyError as e:
        session.rollback()
        if e.orig.diag.message_primary == 'SeatsNoMore':
            return False
        return False

    return True

"""
Funzione per gli studenti per annullare la prenotazione in aula di una lezione frontale
"""      
def delete_reservation(frontalLesson_id):
    try:
        session = Session(bind=get_engine())
        if session.query(Reservation).filter(and_(Reservation.FrontalLessonID == frontalLesson_id, Reservation.StudentID == current_user.get_id())).first().HasValidation == False:
            session.query(Reservation).filter(and_(Reservation.FrontalLessonID == frontalLesson_id, Reservation.StudentID == current_user.get_id())).delete()
            session.commit()
        else:
            return False
    except Exception as e:
        session.rollback()
        return False
    return True

"""
Ritorna un oggetto di tipo reservation dato il suo token
"""
def get_reservation_from_token(token):
    try:
        session = Session(bind=get_engine())
        return session.query(Reservation).filter(Reservation.ReservationID == token).first()
    except Exception as e:
        print(e)
        return None

"""
Funzione per confermare la presenza di uno studente ad una lezione frontale (viene cambiato hasvalidation a true della prenotazione e poi viene creata la relazione
student-lesson)
"""
def confirm_attendance(reservation):
    try:
        session = Session(bind=get_engine())
        session.query(Reservation).filter(and_(Reservation.StudentID == reservation.StudentID, Reservation.FrontalLessonID == reservation.FrontalLessonID)).update({Reservation.HasValidation : True})
        session.commit()
        formalize_student(reservation.StudentID, reservation.FrontalLessonID)
    except Exception as e:
        session.rollback()
"""Viene creata la relazione student-lesson"""
def formalize_student(user_id, lesson_id):
    try:
        session = Session(bind=get_engine())
        session.add(StudentLesson(StudentID = user_id, LessonID = lesson_id))
        session.commit()
    except Exception as e:
        session.rollback()

"""Funzione che ritorna un oggetto di tipo Lesson dato il suo token"""
def get_lesson_from_token(token):
    try:
        session = Session(bind=get_engine())
        return session.query(Lesson).filter(Lesson.Token == token).first()
    except:
        session.rollback()
        session.close()
"""Funzione che ritorna tutte le aule disponibili"""
def get_classrooms():
    try:
        session = Session(bind=get_engine())
        return session.query(Classroom).order_by(Classroom.Name).all()
    except Exception as e:
        print(e)
        session.rollback()
        return []
"""Funzione che ritorna tutte le scuole registrate nel database"""
def get_schools():
    try:
        session = Session(bind=get_engine())
        return session.query(School).all()
    except:
        return []

"""Funzione che ritorna le scuole che contengono un determinato nome passato in input"""
def get_schools_with_name(name):
    try:
        session = Session(bind=get_engine())
        return session.query(School).filter(School.SchoolName.contains(name)).order_by(School.City).all()
    except:
        return []

"""Funzione che ritorna un oggetto di tipo School dato il suo ID"""
def get_school_by_id(school_id):
    try:
        session = Session(bind=get_engine())
        return session.query(School).filter(School.SchoolID == school_id).first()
    except Exception as e:
        print(e)
        return None

"""
Funzione chiamata dai professori che serve per mandare l'attestato di partecipazione a tutti gli studenti che rispettano i requisiti minimi, ovvero
a tutti quei studenti che hanno seguito al più le ore minime richieste per ottenere il certificato
"""
def send_certificate_to_students(course_id):        
    
    # hours = session.query(Course).filter(Course.CourseID == course_id.upper()).first().MinHourCertificate
    hours = get_course_by_id(course_id).MinHourCertificate
    # student_courses = session.query(StudentCourse).filter(course_id == StudentCourse.CourseID).all()
    student_courses = get_students_by_course(course_id)

    for student in student_courses:
        students_courses_hours = get_student_courses(student.UserID) #dentro i corsi dello studente ci salviamo ANCHE  quante ore ha seguito di suddetto corso
        for course in students_courses_hours:
            if course.CourseID == course_id.upper() and course.Hours.total_seconds()/3600 >= hours:
                try:
                    session = Session(bind=get_engine())
                    session.add(Certificate(StudentID = student.UserID, CourseID = course_id.upper(), Hours = course.Hours.total_seconds()/3600))
                    session.commit()     
                except exc.SQLAlchemyError as e:
                    session.rollback()
                finally:
                    session.close()

"""
Funzione chiamata da uno studente per visualizzare tutti i suoi certificati
"""
def get_student_certificates(user_id):
    try:
        session = Session(bind=get_engine())
        return session.query(User.Name.label("StudentName"), Certificate.StudentID, Certificate.CourseID, Certificate.CertificateID, Certificate.Hours, Course.Name, Course.MinHourCertificate)\
            .join(Course, Course.CourseID == Certificate.CourseID)\
            .join(User, User.UserID == Certificate.StudentID)\
            .filter(Certificate.StudentID == user_id).all()
    except Exception as e:
        print(e)
        return None

"""
Funzione chiamata da uno studente per veririficare se uno studente può inviare un feedback
NB : che uno studente può inviare SOLO UN feedback per corso
"""
def can_student_send_feedback(user_id, course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(StudentCourse).filter(and_(StudentCourse.CourseID == course_id, StudentCourse.StudentID == user_id, StudentCourse.HasSentFeedback == False)).first() is not None
    except Exception as e:
        return False
"""
Funzione per studenti per inviare i feedback
"""
def send_feedback(form, course_id):
    try:
        session = Session(bind=get_engine())
        session.add(Feedback(CourseID = course_id, CourseGrade = form.course_grade.data, TeacherGrade = form.teacher_grade.data, Comment = form.comments.data))
        session.commit()
        session.query(StudentCourse).filter(StudentCourse.CourseID == course_id.upper(), StudentCourse.StudentID == current_user.get_id()).update({StudentCourse.HasSentFeedback : not_(StudentCourse.HasSentFeedback)})
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()

"""
Funzione per professori per ottenere la media dei voti che gli studenti hanno mandato nei feedback di un determinato corso
"""
def avg_feedback(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(func.avg(Feedback.CourseGrade).label("CourseGrade"), func.avg(Feedback.TeacherGrade).label("TeacherGrade")).filter(Feedback.CourseID == course_id).first()
    except Exception as e:

        return None

"""
Funzione per ottenere invece tutti i commenti che gli studenti hanno mandato durante il feedback di un determinato corso
"""
def feedback_comments(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Feedback).filter(and_(Feedback.CourseID == course_id, Feedback.Comment.isnot(None))).all()
    except:
        return []

"""
Funzione che conta tutti gli studenti suddivisi per gender
"""
def gender_subscribed(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(func.sum(case((and_(User.Gender.isnot(None), User.Gender == "Male"), 1), else_=0)).label("Male"),\
            func.sum(case((and_(User.Gender.isnot(None), User.Gender == "Female"), 1), else_=0)).label("Female"),\
            func.sum(case((and_(User.Gender.isnot(None), User.Gender == "Non Binary"), 1), else_=0)).label("NonBinary"), \
            func.sum(case((and_(User.Gender.isnot(None), User.Gender == "Other"), 1), else_=0)).label("Other"))\
            .join(StudentCourse, User.UserID == StudentCourse.StudentID).filter(StudentCourse.CourseID == course_id).first()
    except Exception as e:
        print(e)
        return None
"""
Funzione per ottenere tutte le date di nascita degli studenti iscritti ad un corso
"""
def age_subscribed(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Student.birthDate).join(StudentCourse, StudentCourse.StudentID == Student.UserID).filter(StudentCourse.CourseID == course_id).all()
    except:
        return []

"""
funzione per ottenere tutte le città degli studenti iscritti ad un corso
"""
def city_subscribed(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(Student.City).join(StudentCourse, StudentCourse.StudentID == Student.UserID).filter(StudentCourse.CourseID == course_id).all()
    except:
        return
"""
funzione che conta i 3 tipi di scuole degli studenti iscritti ad un corso.
"""
def type_school_subscribed(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(func.sum(case((and_(School.Type.contains("LICEO"), School.Type.isnot(None)), 1), else_=0)).label("Liceo"),\
            func.sum(case((and_(School.Type.contains("ISTITUTO TECNICO"), School.Type.isnot(None)), 1), else_=0)).label("Tecnico"),\
            func.sum(case((and_(School.Type.contains("PROFESSIONALE"), School.Type.isnot(None)), 1), else_=0)).label("Professionale"), \
            func.sum(case((and_(and_(not_(School.Type.contains("LICEO")), not_(School.Type.contains("ISTITUTO TECNICO")), not_(School.Type.contains("PROFESSIONALE"))), School.Type.isnot(None)), 1), else_=0)).label("Altro"))\
            .join(Student, Student.SchoolID == School.SchoolID)\
            .join(StudentCourse, and_(StudentCourse.StudentID == Student.UserID, StudentCourse.CourseID == course_id))\
            .first()
    except Exception as e:
        return None

"""
Funzione che ritorna quante ore di lezioni hanno seguito tutti gli studenti iscritti ad un determianto corso
"""
def hours_attended(course_id):
    try:
        session = Session(bind=get_engine())
        q1 = session.query(func.sum(case((and_(Lesson.StartTime.isnot(None), Lesson.EndTime.isnot(None)), Lesson.EndTime-Lesson.StartTime), else_="00:00:00")).label("Hours"))\
            .join(StudentLesson, StudentLesson.LessonID == Lesson.LessonID)\
            .filter(Lesson.CourseID == course_id)\
            .group_by(StudentLesson.StudentID).all()
        
        return q1

    except exc.SQLAlchemyError as e:
        print(e)
        return []

"""
Funzione che ritorna tutte le domande principali del forum di un determinato corso
"""
def get_questions_by_course(course_id):
    try:
        session = Session(bind=get_engine())
        return session.query(QnA.Text, QnA.TextID, QnA.Date, QnA.Time, QnA.RefTo, User.Name, User.Surname, User.UserID, User.email)\
                    .join(User, User.UserID == QnA.UserID)\
                    .filter(and_(QnA.RefTo.is_(None), QnA.CourseID == course_id))\
                    .order_by(QnA.Date.desc(), QnA.Time.desc())\
                    .all()
    except Exception as e:
        return None

"""
funzione che controlla se un utente è il creatore di una domanda o post
"""
def is_user_owner_post(user_id, post_id):
    try:
        session = Session(bind=get_engine())
        return session.query(QnA).filter(and_(QnA.UserID == user_id, QnA.TextID == post_id)).first() is not None
    except:
        return False
"""
Funzione per eliminare una domanda o post
"""
def delete_post(post_id):
    try:
        session = Session(bind=get_engine())
        session.query(QnA).filter(QnA.TextID == post_id).delete()
        session.commit()
    except:
        session.rollback()
"""
Funzione per aggiungere un post, che essa sia domanda o risposta è indifferente
"""
def add_post(form, course_id):
    try:
        session = Session(bind=get_engine())
        session.add(QnA(Text = form.text.data, 
                        UserID = current_user.get_id(), 
                        RefTo = form.ref_to.data, 
                        CourseID = course_id, 
                        Date = datetime.datetime.today().date(), 
                        Time = datetime.datetime.today().time()))  
        session.commit()
    except Exception as e:
        session.rollback()   


"""
Funzione per fare l'update di un post
"""
def update_post(text, post_id):
    try:
        session = Session(bind=get_engine())
        session.query(QnA).filter(QnA.TextID == post_id).update({QnA.Text : text})
        session.commit()
    except:
        session.rollback()
        return False
    return True
"""
Funzione per i professori per aggiornare tutte le informazioni disponibili di una lezione, cambiandone anche il tipo, da frontale a online, da online a frontale 
ecc ecc. 
Eliminando o aggiornando le relative lezioni nel database ove non più necessarie.
"""
def update_lesson(lesson_id, form):
    try:
        session = Session(bind=get_engine())
        
        is_current_lesson_frontal = session.query(FrontalLesson).filter(FrontalLesson.LessonID == lesson_id).first() is not None
        is_current_lesson_online = session.query(OnlineLesson).filter(OnlineLesson.LessonID == lesson_id).first() is not None
        
        is_current_lesson_dual = is_current_lesson_frontal and is_current_lesson_online

        is_new_lesson_dual = True if form.lesson_type_update.data == 'Duale' else False
        
        if form.lesson_type_update.data == "Frontale" and (is_current_lesson_dual or is_current_lesson_online):     
            session.query(OnlineLesson).filter(OnlineLesson.LessonID == lesson_id).delete()      
            session.query(FrontalLesson).filter(FrontalLesson.LessonID == lesson_id).update({FrontalLesson.ClassroomID : form.classroom_update.data})
            if not is_current_lesson_frontal:
                session.add(FrontalLesson(LessonID = lesson_id, ClassroomID = form.classroom_update.data))
        
        elif form.lesson_type_update.data == "Online" and (is_current_lesson_frontal or is_current_lesson_dual):
            session.query(FrontalLesson).filter(FrontalLesson.LessonID == lesson_id).delete()
            session.query(OnlineLesson).filter(OnlineLesson.LessonID == lesson_id).update({OnlineLesson.RoomLink : form.link_update.data, OnlineLesson.RoomPassword : form.password_update.data})
            if not is_current_lesson_online:
                session.add(OnlineLesson(LessonID = lesson_id, RoomLink = form.link_update.data, RoomPassword = form.password_update.data))
        
        elif form.lesson_type_update.data == "Duale" and not is_current_lesson_online:
            session.add(OnlineLesson(LessonID= lesson_id, RoomLink=form.link_update.data, RoomPassword = form.password_update.data))
            session.query(FrontalLesson).filter(FrontalLesson.LessonID == lesson_id).update({FrontalLesson.ClassroomID : form.classroom_update.data})
        
        elif form.lesson_type_update.data == "Duale" and not is_current_lesson_frontal:
            session.add(FrontalLesson(LessonID=lesson_id, ClassroomID = form.classroom_update.data))
            session.query(OnlineLesson).filter(OnlineLesson.LessonID == lesson_id).update({OnlineLesson.RoomLink : form.link_update.data, OnlineLesson.RoomPassword : form.password_update.data})
      
        session.query(Lesson).filter(Lesson.LessonID == lesson_id).update({Lesson.Date : form.date_update.data, Lesson.StartTime : form.start_time_update.data, Lesson.EndTime : form.end_time_update.data, Lesson.IsDual : is_new_lesson_dual})
        session.commit()
        
    except exc.SQLAlchemyError as e:
        session.rollback()
        
        if e.orig.diag.message_primary == "LessonOverlapping":
            flash("Lesson overlapping error")
            # delete_lesson(lesson_new.LessonID)
            return "ClashError"

        if e.orig.diag.message_primary == "SameCourseOverlapping":
            flash("Lesson overlapping error")
            return "SameCourseClashError"

        if e.orig.pgcode == '23514': #check constraint error
            flash("Date error")
            return "DataError"
        
        flash("Unknown error")
        return "UnknownError"
        
    finally:
        session.close()
    
    return "Success"

"""
Ritorna tutte le risposte ad una domanda dato il suo ID
"""
def get_answers_by_question_id(question_id):
    try:
        session = Session(bind=get_engine())
        return session.query(QnA.Text, QnA.TextID, QnA.RefTo, QnA.Date, QnA.Time, User.Name, User.Surname, User.UserID, User.email).join(User, User.UserID == QnA.UserID).filter(QnA.RefTo == question_id).order_by(QnA.Date, QnA.Time).all()
    except:
        return []

"""
Aggiorna la password di un utente
"""
def update_user_psw(user_id, psw):
    try:
        session=Session(bind = get_engine())
        session.query(User).filter(User.UserID == user_id).update({User.Password : generate_password_hash(psw).decode("utf-8")})
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()