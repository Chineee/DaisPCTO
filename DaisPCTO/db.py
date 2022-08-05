from DaisPCTO.models import Feedback,\
     ProfessorCourse, StudentCourse, User, Student, Professor,\
     UserRole, Course, Role, Lesson, StudentLesson, Reservation, \
     FrontalLesson, OnlineLesson, Classroom
from sqlalchemy import create_engine, and_, not_, or_, not_, exc, func, case
from sqlalchemy.orm import sessionmaker
from flask_login import current_user, user_accessed
from flask_bcrypt import generate_password_hash, check_password_hash
import random 

engine = {
    "Admin" : create_engine("postgresql://postgres:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0),
    "Student" : create_engine("postgresql://Student:studente01@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Professor" : create_engine("postgresql://Professor:123456@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Anonymous" : create_engine("postgresql://Anonymous:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0)
}

# studente = create_engine("postgresql://Student:ewfdwefd@localhost/testone8",echo=False, pool_size=20, max_overflow=0)
# engine2 = create_engine("postgresql://Student:studente01@localhost/testone8", echo=False, pool_size=20, max_overflow=0)

Session = sessionmaker(bind=engine['Admin'])


def get_engine():
    if not current_user.is_authenticated:
        return engine["Anonymous"]
    elif current_user.hasRole("Student"):
        return engine["Student"]
    elif current_user.hasRole("Professor"):
        return engine["Professor"]
    elif current_user.hasRole("Admin"):
        return engine["Admin"]
    else:
        return None

def extestone():
    # try:
    #     session=Session()
    #     session.add(Lesson(LessonID=6666))
    #     session.commit()
    # except Exception as e:
    #     print(e.orig.diag.message_primary)
    #     session.rollback()
    
    
    try:
        session = Session()
        utenteGender = session.query(User).filter(User.Gender == 'M').first()
        session.query(User).filter(User.email=='skele@gmail.com').update({User.Gender : 'Female'})
        session.query(User).filter(User.email=='skele@gmail.com').update({User.Name : 'Marca'})
        session.commit()
    except:
        session.rollback()
        #roleList = session.query(Role).all()

def exists_role_user(user_id, role):
    try:
        session = Session()
        return session.query(UserRole).join(Role).filter(and_(UserRole.UserID == user_id, Role.Name == role)).first() is not None
    except:
        return False

def get_course_by_id(course_id):
    try:
        session = Session()
        return session.query(Course).filter(Course.CourseID == course_id).first()
    except:
        return None

def get_user_by_id(id):
    try:
        session = Session()
    # session.connection(execution_options={'isolation_level': 'SERIALIZABLE', "postgresql_readonly" : True})
    # try:
    #     session.add(User(UserID=10))
    # except:
    #     session.rollback()
    #     print("roll back")
    # print("OK")
        return session.query(User).filter(User.UserID == id).first()
    except:
        return None

def get_user_id_by_email(email):
    pass

def get_user_email_by_id(userId):
    pass 

def get_user_by_email(email):
    try:
        session = Session()
        return session.query(User).filter(User.email == email).first()
    except:
        return None
    
def create_user(form):

    Name = form.name.data
    Surname = form.surname.data
    Email = form.email.data
    Password = form.password.data
    Gender = form.gender.data
    Phone = form.phone.data
    Address = form.address.data

    new_user = User(Name=Name, Surname=Surname, Gender=Gender, Address = Address, email=Email, Password = generate_password_hash(Password).decode('utf-8'), PhoneNumber=Phone)
    
    return new_user

def add_user(User):
    try:
        session = Session()
        session.add(User)
        session.commit()
        add_student(User)
    except:
        session.rollback()
        return False 
    return True

def add_student(user):

    #MODIFICARE ADD STUDENT IN MODO CHE ADDI TUTTI GLI ALTRI CAMPI

    try:
        session = Session()
        session.add_all([Student(UserID = user.UserID, SchoolID=None), UserRole(UserID = user.UserID, RoleID = 2)])
        session.commit()
    except:
        session.rollback()

def compare_password(db_password, inserted_password):
    return check_password_hash(db_password, inserted_password)

        

def add_course(form):
    
    name = form.name.data
    course_id = form.course_id.data.upper()
    description = form.description.data 
    max_students = form.max_students.data
    min_hours = form.min_hour_certificate.data
    
    try:
        session = Session()
        session.add(Course(OpenFeedback=False, CourseID=course_id, Name=name, Description = description, MaxStudents=max_students, MinHourCertificate = min_hours))
        session.add(ProfessorCourse(CourseID=course_id, ProfessorID=current_user.get_id()))
        session.commit()
    except:
        session.rollback()

#ritorna true se e solo se esiste una tupla che contenga l'id del professore e l'id del corso all'interno della tabella professorcourse
def can_professor_modify(prof_id, course_id):
    try:
        session = Session()
        return session.query(ProfessorCourse).filter(and_(ProfessorCourse.ProfessorID == prof_id, ProfessorCourse.CourseID == course_id)).first() is not None
    except:
        return False

def get_professor_by_course_id(course_id):
    try:
        session = Session()
        return session.query(User).filter(and_(ProfessorCourse.CourseID == course_id, ProfessorCourse.ProfessorID == User.UserID)).all()
    except:
        session.close()
        return None

# select user
# from ( user u natural join professor p ) natural join professorcourse pc
# where pc.courseid = 'id'

def count_student(course_id):
    try:
        session = Session()

        return session.query(StudentCourse).filter(StudentCourse.CourseID == course_id).count()
    except:
        return None

def change_course_attr(form, course_id):
    try:
        session = Session()
        
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

def change_feedback(course_id):
    try: 
        session = Session()       
        session.query(Course).filter(Course.CourseID == course_id).update({Course.OpenFeedback : not_(Course.OpenFeedback)})
        session.commit()
    except:
        session.rollback()
    finally:
        session.close()

def subscribe_course(student_id, course_id):
    try:
        session = Session()
        session.add(StudentCourse(StudentID=student_id, CourseID=course_id))
        session.commit()
    except:
        session.rollback()

def is_subscribed(student_id, course_id):
    try:
        session = Session()
        
        if session.query(StudentCourse).filter(and_(StudentCourse.StudentID == student_id, StudentCourse.CourseID == course_id)).first() is None:
            return False
        return True
    except:
        return False

def delete_subscription(student_id, course_id): 
    try:
        session = Session()      

        session.query(StudentCourse).filter(and_(StudentCourse.StudentID == student_id, StudentCourse.CourseID == course_id)).delete()
        session.commit()
    except:
        session.rollback()

def add_lesson(form, course_id, professor):
    date = form.date.data
    start_time = form.start_time.data
    end_time = form.end_time.data
    topic = form.topic.data
    type_lesson = form.type_lesson.data
    is_dual = True if type_lesson == "Duale" else False
    classroom = form.classroom.data
    token = generate_password_hash(f'{current_user.get_id()}{course_id}{date}{start_time}{end_time}{classroom}{random.randint(0, 501)}')
     
    try:
        session = Session()
        lesson_new = Lesson(Date = date, StartTime = start_time, EndTime = end_time, Topic = topic, IsDual = is_dual, CourseID = course_id, ProfessorID=professor, Token=token)
        session.add(lesson_new)
        session.flush()
        if (type_lesson == "Frontale"):
            session.add(FrontalLesson(LessonID = lesson_new.LessonID , ClassroomID = classroom))
        elif (type_lesson == "Online"):
            session.add(OnlineLesson(LessonID=lesson_new.LessonID))
        elif (type_lesson == "Duale"):
            session.add(FrontalLesson(LessonID = lesson_new.LessonID , ClassroomID = classroom))
            session.add(OnlineLesson(LessonID=lesson_new.LessonID))

        session.commit()
    except exc.SQLAlchemyError as e:

       
        '''
        NB: 23514 È IL CODICE CHE INDICA UN "psycopg2.errors.CheckViolation" quindi se l'errore corrisponde a quel codice significa che stiamo
        violando l'unico checkconstrain della tabella lesson, ovvero quello della data di inizio che deve essere strettamente minore della data di
        fine
        '''

            
        if int(e.orig.pgcode) == 23514: 
            return "DateError"

        '''
        NB: Messaggio di un eccezione lanciamo noi
        '''

        if e.orig.diag.message_primary == "Classroom is already taken":
            return "ClashError"
        
        return "UnknownError"

    return "Success"

def delete_lesson(lesson_id):
    try:
        session = Session()
        session.query(Lesson).filter(Lesson.LessonID == lesson_id).delete()
        session.commit()
    except Exception as e:
        print(e)
        session.rollback()
        return False 
    return True

def get_lessons_by_course_id(course_id):
    try:
        session = Session()
        return session.query(Lesson).filter(Lesson.CourseID == course_id).order_by(Lesson.Date, Lesson.StartTime).all()
    except:
        return None

def get_course_id_by_lesson_id(lesson_id):
    try:
        session = Session()
        return session.query(Course).filter(and_(Lesson.LessonID == lesson_id, Course.CourseID == Lesson.CourseID)).first().CourseID
    except:
        return None
        
def can_reserve(user_id, lesson_id):
    try:
        session = Session()
        num_reserved = session.query(Reservation).filter(Reservation.FrontalLessonID == lesson_id).count()
        classroom_seats = session.query(Classroom.Seats).filter(FrontalLesson.LessonID == lesson_id, Classroom.ClassroomID == FrontalLesson.ClassroomID)
        # return session.query(Reservation).filter(and_(Reservation.StudentID == user_id, Reservation.FrontalLessonID == lesson_id, Lesson.LessonID == Reservation.FrontalLessonID, Lesson.Token == token)).first() is not None  
        if classroom_seats > num_reserved:
            token = None #unione di una serie di cose che ora non abbiamo voglia di fare hashate
            session.add(Reservation(StudentID = user_id, FrontalLessonID = lesson_id, HasValidation = False, ReservationID = token))
            return True
        else:
            return False
    except:  
        return False


def confirm_attendance(user_id, lesson_id, lesson_token):
    try:
        session = Session()
        if session.query(Reservation).filter(Reservation.FrontalLessonID == lesson_id, Reservation.ReservationID == lesson_token, Reservation.StudentID == user_id, Reservation.HasValidation == False).first() is not None:
            session.query(Reservation).filter(and_(Reservation.FrontalLessonID == lesson_id, Reservation.StudentID == user_id)).update({Reservation.HasValidation : True})
            session.commit()
    except:
        session.rollback()
        return False
    return True

def change_lesson_information(lesson_id, data):
    try:
        session = Session() 
        session.query(Lesson).filter(Lesson.LessonID == lesson_id).update({Lesson.Topic : data})
        session.commit()
    except:
        session.rollback()
        return False 
    return True

def get_courses_list():
    try:
        session = Session()
        return session.query(Course).order_by(Course.Name).all()
    except:
        return None

def get_professor_courses(user_id):
    try:
        session = Session()
        # if not is_professor:
        #     return session.query(Course)\
        #         .join(StudentCourse)\
        #         .filter(StudentCourse.StudentID == user_id)\
        #         .order_by(Course.Name)\
        #         .all()
        # else:
        return session.query(Course)\
            .join(ProfessorCourse)\
            .filter(ProfessorCourse.ProfessorID == user_id)\
            .order_by(Course.Name)\
            .all()
    except:
        return None


def get_student_courses(user_id):
    try:
        print("INIT QUERY")
        session = Session()
        # return session.query(Course.CourseID, Course.Name, func.sum(Lesson.EndTime - Lesson.StartTime).label("Hours"))\
        #         .join(StudentCourse)\
        #         .join(StudentLesson)\
        #         .join(Lesson)\
        #         .filter(StudentCourse.StudentID == user_id)\
        #         .order_by(Course.Name)\
        #         .group_by(Course.CourseID, Course.Name).all()
        query = session.query(Course.CourseID, Course.Name, Course.Description, Course.MaxStudents, Course.MinHourCertificate, func.sum(case((and_(Lesson.StartTime.isnot(None), Lesson.EndTime.isnot(None)), Lesson.EndTime-Lesson.StartTime), else_="00:00:00")).label("Hours")) \
                    .join(StudentCourse, StudentCourse.CourseID == Course.CourseID)\
                    .join(StudentLesson, StudentLesson.StudentID == StudentCourse.StudentID, isouter=True)\
                    .join(Lesson, and_(Lesson.LessonID == StudentLesson.LessonID, Lesson.CourseID == Course.CourseID), isouter=True)\
                    .filter(StudentCourse.StudentID == user_id)\
                    .order_by(Course.Name)\
                    .group_by(Course.CourseID, Course.Name, Course.Description, Course.MaxStudents, Course.MinHourCertificate).all()



        print("END QUERY")
        return query

    except Exception as e:
        print(e)

        return []

"""

SELECT "Courses"."CourseID", SUM(CASE WHEN ("Lessons"."StartTime" IS NOT NULL AND "Lessons"."EndTime" IS NOT NULL) THEN "Lessons"."EndTime" - "Lessons"."StartTime" ELSE '00:00:00' END)
FROM "StudentsCourses" NATURAL JOIN "Courses" NATURAL LEFT JOIN ("Lessons" NATURAL LEFT JOIN "StudentsLessons")
WHERE "StudentsCourses"."StudentID" = 1
GROUP BY "Courses"."CourseID"


FROM "Courses" NATURAL JOIN "StudentsCourses" NATURAL LEFT JOIN "StudentsLessons" NATURAL LEFT JOIN "Lessons"

FROM "Courses" LEFT OUTER JOIN "Lessons" ON "Courses"."CourseID" = "Lessons"."CourseID" LEFT OUTER JOIN "StudentsLessons" ON "Lessons"."LessonID" = "StudentsLessons"."LessonID" JOIN "StudentsCourses" ON "Courses"."CourseID" = "Stude
ntsCourses"."CourseID"



"""
