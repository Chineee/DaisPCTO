from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, String, Integer, Date, ForeignKey, CheckConstraint, Time, Boolean, or_, and_, UniqueConstraint, Text, Float
from sqlalchemy.orm import relationship
from flask_login import UserMixin

Base = declarative_base()

class User(Base, UserMixin):
    __tablename__ = "Users"

    UserID = Column(Integer, primary_key=True)
    Name = Column(String)
    Surname = Column(String)
    Gender = Column(String)
    email = Column(String, unique=True)
    Password = Column(String)
    PhoneNumber = Column(String)

    Roles = relationship('Role', secondary = "user_role")
    Posts = relationship("QnA", backref = "User")

    __table_args__ = (
        CheckConstraint(or_(Gender == 'Female', Gender=='Male', Gender=='Non Binary', Gender == 'Other')),
    )

    def get_id(self):
        return self.UserID

    def hasRole(self, role):
        
        from DaisPCTO.db import exists_role_user #per evitare il circular import va messo dentro la funzione
        return exists_role_user(self.get_id(), role)

class Student(Base):
    __tablename__ = "Students"

    UserID = Column(Integer, ForeignKey("Users.UserID", ondelete='CASCADE'), primary_key=True)
    SchoolID = Column(Integer, ForeignKey("Schools.SchoolID"))
    birthDate = Column(Date)
    SchoolYear = Column(Integer)
    City = Column(String)
    Address = Column(String)
    
    __table_args__ = ()

class Professor(Base):
    __tablename__ = "Professors"

    UserID = Column(Integer, ForeignKey("Users.UserID", ondelete='CASCADE'), primary_key=True)

    LessonsList = relationship("Lesson", backref="Professor")

    __table_args__ = ()

class School(Base):
    __tablename__ = "Schools"

    SchoolID = Column(Integer, primary_key=True)
    SchoolName = Column(String)
    Address = Column(String)
    City = Column(String)
    Region = Column(String)
    Type = Column(String)

    Students = relationship("Student", backref = "School")

    __table_args__ = (UniqueConstraint(SchoolName, Address, City),)

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
    Description = Column(Text)
    MaxStudents = Column(Integer)
    MinHourCertificate = Column(Integer)
    OpenFeedback = Column(Boolean)
    
    Professors = relationship("Professor", secondary="ProfessorsCourses", backref="Courses")
    Students = relationship("Student", secondary="StudentsCourses", backref="Courses")


    __table_args__ = ()

    def hasStudent(self, student):

        for s in self.Students:
            if s.UserID == student.UserID:
                return True 
        return False

class Certificate(Base):
    __tablename__ = "Certificates"

    CertificateID = Column(Integer, primary_key=True)
    StudentID = Column(Integer, ForeignKey("Students.UserID"), unique = True)
    CourseID = Column(String, ForeignKey("Courses.CourseID"), unique = True)
    Hours = Column(Float)

    Students = relationship("Student", backref="Certificates")
    Courses = relationship("Course", backref="Certificates")

    __table_args__ = ()

class StudentCourse(Base):
    __tablename__ = "StudentsCourses"

    CourseID = Column(String, ForeignKey("Courses.CourseID"), primary_key=True)
    StudentID = Column(Integer, ForeignKey("Students.UserID", ondelete='CASCADE'), primary_key=True)
    HasSentFeedback = Column(Boolean)

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
    Comment = Column(Text)

    Courses = relationship("Course", backref="Feedbacks")

    __table_args__ = (
        CheckConstraint(CourseGrade >= 0),
        CheckConstraint(TeacherGrade >= 0),
    )

class Lesson(Base):
    __tablename__ = "Lessons"

    LessonID = Column(Integer, primary_key=True)
    CourseID = Column(String, ForeignKey("Courses.CourseID"))
    ProfessorID = Column(Integer, ForeignKey("Professors.UserID"))
    Date = Column(Date)
    StartTime = Column(Time)
    EndTime = Column(Time)
    Topic = Column(Text)
    Token = Column(String, unique=True)
    IsDual = Column(Boolean)

    __table_args__ = (
        CheckConstraint(StartTime < EndTime),
    )

    Students = relationship("Student", secondary="StudentsLessons", backref="Lessons")

class StudentLesson(Base):
    __tablename__ = "StudentsLessons"

    StudentID = Column(Integer, ForeignKey("Students.UserID"), primary_key=True)
    LessonID = Column(Integer, ForeignKey("Lessons.LessonID", ondelete='CASCADE'), primary_key=True)

    __table_args__ = ()

class FrontalLesson(Base):
    __tablename__ = "FrontalLessons"

    __table_args__ = ()

    LessonID = Column(Integer, ForeignKey("Lessons.LessonID", ondelete="CASCADE"), primary_key=True)
    ClassroomID = Column(Integer, ForeignKey("Classrooms.ClassroomID"))

    Classroom = relationship("Classroom", backref = "Lessons")

class Classroom(Base):
    __tablename__ = "Classrooms"

    ClassroomID = Column(Integer, primary_key=True)
    Name = Column(String)
    Seats = Column(Integer)
    Floor = Column(Integer)
    Building = Column(String)
    Address = Column(String)

    __table_args__ = (
        CheckConstraint(Seats > 0),
        CheckConstraint(Floor >= 0),
        UniqueConstraint(Name, Building)
    )

class OnlineLesson(Base):
    __tablename__ = "OnlineLessons"

    LessonID = Column(Integer, ForeignKey("Lessons.LessonID", ondelete="CASCADE"), primary_key=True)
    RoomLink = Column(String)
    RoomPassword = Column(String)

    __table_args__ = ()

class QnA(Base):
    __tablename__ = "QnA"

    TextID = Column(Integer, primary_key=True)
    RefTo = Column(Integer, ForeignKey("QnA.TextID", ondelete='CASCADE', onupdate='CASCADE'))
    CourseID = Column(String, ForeignKey("Courses.CourseID", ondelete='CASCADE', onupdate='CASCADE'))
    UserID = Column(Integer, ForeignKey("Users.UserID", ondelete='CASCADE', onupdate='CASCADE'))
    Text = Column(Text)
    Date = Column(Date)
    Time = Column(Time)
    
    Courses = relationship("Course", backref="Questions")
    Answers = relationship("QnA")

    __table_args__ = ()


class Reservation(Base):
    __tablename__ = "Reservation"

    StudentID = Column(Integer, ForeignKey("Students.UserID", ondelete='CASCADE'), primary_key=True)
    FrontalLessonID = Column(Integer, ForeignKey("FrontalLessons.LessonID", ondelete='CASCADE'), primary_key=True)
    ReservationID = Column(String, unique=True) 
    HasValidation = Column(Boolean)

    __table_args__= ()