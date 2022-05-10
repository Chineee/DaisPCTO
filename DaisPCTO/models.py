from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer, String, Column, Date 
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from sqlalchemy import *
from sqlalchemy.orm import *

engine = create_engine("postgresql://postgres:123456@localhost/testone2", echo=True)

Base = declarative_base()

Session = sessionmaker(bind=engine)
session = Session()

class User(Base, UserMixin):
    __tablename__ = "Users"

    UserID = Column(Integer, primary_key=True)
    Name = Column(String)
    Surname = Column(String)
    Gender = Column(String)
    Address = Column(String)
    email = Column(String, unique=True)
    Password = Column(String)
    PhoneNumber = Column(String)

    Roles = relationship('Role', secondary = "user_role")

    __table_args__ = (
        CheckConstraint(or_(Gender == 'Female', Gender=='Male', Gender=='Non Binary', Gender == 'Other')),
    )

class Student(Base):
    __tablename__ = "Students"

    UserID = Column(Integer, ForeignKey("Users.UserID"), primary_key=True)
    SchoolID = Column(Integer, ForeignKey("Schools.SchoolID"))
    birthDate = Column(Date)
    SchoolYear = Column(Integer)

    __table_args__ = ()

class Professor(Base):
    __tablename__ = "Professors"

    UserID = Column(Integer, ForeignKey("Users.UserID"), primary_key=True)

    __table_args__ = ()

class School(Base):
    __tablename__ = "Schools"

    SchoolID = Column(Integer, primary_key=True)
    Address = Column(String)
    City = Column(String)
    OfficesContacts = Column(String)

    Students = relationship("Student", backref = "School")

    __table_args__ = ()

class Role(Base):
    __tablename__ = "roles"

    RoleID = Column(Integer, primary_key=True)
    Name = Column(String)

    __table_args__ = ()

class UserRole(Base):
    __tablename__ = 'user_role'

    RoleID= Column(Integer, ForeignKey("roles.RoleID", ondelete="CASCADE"), primary_key=True)
    UserID = Column(Integer, ForeignKey("Users.UserID", ondelete="CASCADE"), primary_key=True)

    __table_args__ = ()

class Course(Base):
    __tablename__ = "Courses"

    CourseID = Column(String, primary_key=True)
    Name = Column(String)

    Professors = relationship("Professor", secondary="ProfessorsCourses", backref="Courses")
    Students = relationship("Student", secondary="StudentsCourses", backref="Courses")

    __table_args__ = ()

class Certificate(Base):
    __tablename__ = "Certificates"

    CertificateID = Column(Integer, primary_key=True)
    StudentID = Column(Integer, ForeignKey("Students.UserID"))
    CourseID = Column(String, ForeignKey("Courses.CourseID"))
    Hours = Column(Integer)

    Students = relationship("Student", backref="Certificates")
    Courses = relationship("Course", backref="Certificates")

    __table_args__ = ()

class StudentCourse(Base):
    __tablename__ = "StudentsCourses"

    CourseID = Column(String, ForeignKey("Courses.CourseID"), primary_key=True)
    StudentID = Column(Integer, ForeignKey("Students.UserID"), primary_key=True)

    __table_args__ = ()

class ProfessorCourse(Base):
    __tablename__ = "ProfessorsCourses"

    CourseID = Column(String, ForeignKey("Courses.CourseID"), primary_key=True)
    ProfessorID = Column(Integer, ForeignKey("Professors.UserID"), primary_key=True)

    __table_args__ = ()

class Feedback(Base):
    __tablename__ = "Feedbacks"

    FeedbackID = Column(Integer, primary_key=True)
    CourseID = Column(String, ForeignKey("Courses.CourseID"))
    CourseGrade = Column(Integer)
    TeacherGrade = Column(Integer)

    Courses = relationship("Course", backref="Feedbacks")

    __table_args__ = (
        CheckConstraint(CourseGrade >= 0),
        CheckConstraint(TeacherGrade >= 0),
    )

class Lesson(Base):
    __tablename__ = "Lessons"

    LessonID = Column(Integer, primary_key=True)
    CourseID = Column(String, ForeignKey("Courses.CourseID"))
    Date = Column(Date)
    StartTime = Column(Time)
    EndTime = Column(Time)
    Topic = Column(String)
    Token = Column(String, unique=True)
    IsDual = Column(Boolean)

    __table_args__ = (
        CheckConstraint(StartTime < EndTime),
    )

    Students = relationship("Student", secondary="StudentsLessons", backref="Lessons")

class StudentLesson(Base):
    __tablename__ = "StudentsLessons"

    StudentID = Column(Integer, ForeignKey("Students.UserID"), primary_key=True)
    LessonID = Column(Integer, ForeignKey("Lessons.LessonID"), primary_key=True)

    __table_args__ = ()

class FrontalLesson(Base):
    __tablename__ = "FrontalLessons"

    __table_args__ = ()

    LessonID = Column(Integer, ForeignKey("Lessons.LessonID"), primary_key=True)
    ClassroomID = Column(Integer, ForeignKey("Classrooms.ClassroomID"))

    Classroom = relationship("Classroom", backref = "Lessons")

class Classroom(Base):
    __tablename__ = "Classrooms"

    ClassroomID = Column(Integer, primary_key=True)
    Name = Column(String)
    Seats = Column(Integer)
    Floor = Column(Integer)
    Building = Column(String)

    __table_args__ = (
        CheckConstraint(Seats > 0),
        CheckConstraint(Floor >= 0),
        UniqueConstraint(Name, Building)
    )


class OnlineLesson(Base):
    __tablename__ = "OnlineLessons"

    LessonID = Column(Integer, ForeignKey("Lessons.LessonID"), primary_key=True)
    RoomLink = Column(String)
    RoomPassword = Column(String)

    __table_args__ = ()

class QnA(Base):
    __tablename__ = "QnA"

    TextID = Column(Integer, primary_key=True)
    RefTo = Column(Integer, ForeignKey("QnA.TextID"))
    LessonID = Column(Integer, ForeignKey("Lessons.LessonID"))
    Text = Column(String)

    Lessons = relationship("Lesson", backref="Questions")
    Answers = relationship("QnA")

    __table_args__ = ()

class Material(Base):

    __tablename__ = "Materials"

    MaterialID = Column(Integer, primary_key=True)
    LessonID = Column(Integer, ForeignKey("Lessons.LessonID"))
    MarkDownFile = Column(String)

    Lessons = relationship("Lesson", backref="Materials")

    __table_args__ = ()


app = Flask(__name__)
bcrypt = Bcrypt(app)


session.add_all([Classroom(Seats = 150, Floor = 0, Name = 'Aula 1', Building = 'Zeta'),
                 Classroom(Seats = 150, Floor = 0, Name = 'Aula 2', Building = "Zeta"),
                 Classroom(Seats = 48, Floor = 1, Name = 'Aula A', Building = 'Zeta'),
                 Classroom(Seats = 35, Floor = 0, Name ='Laboratorio 5', Building ='Zeta'),
                 Classroom(Seats = 35, Floor = 0, Name ='Laboratorio 6', Building ='Zeta'),
                 Classroom(Seats = 70, Floor = 1, Name = 'Aula B', Building = 'Zeta'),
                 Classroom(Seats = 90, Floor = 1, Name = 'Aula C', Building = 'Zeta'),
                 Classroom(Seats = 50, Floor = 1, Name = 'Aula D', Building = 'Zeta')])

session.add_all([User(Name='Elisa', Surname='Rizzo', Gender='Female', Address='Francia', email='elisa@gmail.com', Password=bcrypt.generate_password_hash("mylittlepony").decode("utf-8"), PhoneNumber= "347 666 66 56"),
                 User(Name='Marco', Surname='Chinellato', Gender='Male', Address='Lussemburgo', email='skele@gmail.com', Password=bcrypt.generate_password_hash("ediolognomomongoloide").decode("utf-8"), PhoneNumber="23409478904"),
                 User(Name='Davide', Surname='Tonetto', Gender='Male', Address='Seattle', email="tonetto@libero.com", Password=bcrypt.generate_password_hash("solo30elode"), PhoneNumber="666666"),
                 User(Name='Chiara', Surname='Pareschi', Gender='Female', Address='Vaticano', email='pareschirulez@gmail.com', Password=bcrypt.generate_password_hash("abbassogliuominibianchieterocisprivilegiati").decode("utf-8"), PhoneNumber="6666969666"),
                 User(Name='Dumitru', Surname='Zotea', Gender='Other', Address='Terra della Fantasia', email='darkythedragon@gmail.com', Password=bcrypt.generate_password_hash("sonomoltostelthconimieipornofurryneltablet").decode("utf-8"), PhoneNumber='123456')])


session.add_all([School(SchoolID = 1), School(SchoolID = 2), School(SchoolID = 3), School(SchoolID = 4), School(SchoolID = 5)])

session.add_all([Student(UserID=1, SchoolID=1, birthDate='2000-12-05', SchoolYear = 2),
                 Student(UserID=2, SchoolID=1, birthDate=Date(2000, 12, 5), SchoolYear = 2),
                 Student(UserID=3, SchoolID=2, birthDate=Date(2000, 12, 5), SchoolYear = 2),
                 Student(UserID=4, SchoolID=3, birthDate=Date(2000, 12, 5), SchoolYear = 2),
                 Student(UserID=5, SchoolID=4, birthDate=Date(2000, 12, 5), SchoolYear = 2)])

#creare dei docenti e poi basta cominciare con il progetto

session.commit()

if __name__ == "__main__":
    app.run()