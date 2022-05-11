from DaisPCTO.models import User, Student, Professor
from flask_bcrypt import generate_password_hash, check_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("postgresql://postgres:123456@localhost/testone8", echo=True)
Session = sessionmaker(bind=engine)

def create_user(form):

    Name = form.name.data
    Surname = form.surname.data
    Email = form.email.data
    Password = form.password.data
    Gender = form.gender.data
    Phone = form.phone.data
    Address = form.address.data
    BirthDate = form.birthDate.data
    SchoolName = form.schoolName.data
    SchoolCity = form.schoolCity.data
    SchoolYear = form.schoolYear.data

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