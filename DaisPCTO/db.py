from DaisPCTO.models import User, Student, Professor, UserRole
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

engine = create_engine("postgresql://postgres:123456@localhost/testone8", echo=False)
Session = sessionmaker(bind=engine)


def get_user_by_id(id):
    session = Session()
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
    
    