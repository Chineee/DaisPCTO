from DaisPCTO.models import Feedback, ProfessorCourse, StudentCourse, User, Student, Professor, UserRole, Course, Lesson, Role
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, user_accessed
from flask_bcrypt import generate_password_hash, check_password_hash

engine = {
    "Admin" : create_engine("postgresql://postgres:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0),
    "Student" : create_engine("postgresql://Student:studente01@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Professor" : create_engine("postgresql://Professor:123456@localhost/testone8",echo=False, pool_size=20, max_overflow=0),
    "Anonymous" : create_engine("postgresql://Anonymous:123456@localhost/testone8", echo=False, pool_size=20, max_overflow=0)
}

# studente = create_engine("postgresql://Student:ewfdwefd@localhost/testone8",echo=False, pool_size=20, max_overflow=0)
# engine2 = create_engine("postgresql://Student:studente01@localhost/testone8", echo=False, pool_size=20, max_overflow=0)

Session = sessionmaker(bind=engine['Admin'], expire_on_commit = False)

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
   
def get_course_by_id(id):
    session = Session()
    return session.query(Course).filter(Course.CourseID == id).first()

def get_user_by_id(id):
    session = Session()
    # session.connection(execution_options={'isolation_level': 'SERIALIZABLE', "postgresql_readonly" : True})
    # try:
    #     session.add(User(UserID=10))
    # except:
    #     session.rollback()
    #     print("roll back")
    # print("OK")
    return session.query(User).filter(User.UserID == id).first()

def get_user_id_by_email(email):
    pass

def get_user_email_by_id(userId):
    pass 

def get_user_by_email(email):
    session = Session()
    return session.query(User).filter(User.email == email).first()
    
def create_user(form):

    Name = form.name.data
    Surname = form.surname.data
    Email = form.email.data
    Password = form.password.data
    Gender = form.gender.data
    Phone = form.phone.data
    Address = form.address.data

    new_user = User(Name=Name, Surname=Surname, Gender=Gender, Address = Address, email=Email, Password = generate_password_hash(Password), PhoneNumber=Phone)
    
    return new_user

def add_user(User):
    try:
        session = Session()
        session.add(User)
        session.commit()
    except:
        session.rollback()
        return False 
    return True

def compare_password(db_password, inserted_password):
    return check_password_hash(db_password, inserted_password)


def add_course(form):
    
    name = form.name.data
    course_id = form.course_id.data
    description = form.description.data 
    max_students = form.max_students.data
    min_hours = form.min_hours_certificate.data
    
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

def change_course_attr(form):
    if form.description.data is not None:
        Description = form.description.data

def count_student(course_id):
    session = Session()

    return len(session.query(StudentCourse).filter(StudentCourse.CourseID == course_id).all())