from flask_login import login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators, SelectMultipleField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length
from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from flask_mail import Mail, Message
from DaisPCTO.models import *
from DaisPCTO.db import *
from functools import wraps
        
class ProfessorRegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(message="Campo Richiesto")], render_kw={"placeholder":"Nome"})
    surname = StringField('Cognome', validators=[DataRequired(message="Campo Richiesto")], render_kw={"placeholder" : "Cognome"})
    # gender = SelectField('Genere', choices=[("", "--Seleziona un genere--"),("Male", "Male"),("Female", "Female"), ("Non Binary", "NonBinary"), ("Other", "Other")], validators=[DataRequired(message="Campo richiesto")])
    email = EmailField('Email', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Email"})
    # repeat_email = EmailField('Reinserisci Email', validators=[DataRequired(message="Campo richiesto"), EqualTo('email', message='Le email devono corrispondere!')], render_kw={"placeholder":"Ripeti Email"})
    # password = PasswordField(validators=[DataRequired(message="Campo richiesto")])
    # phonenumber = StringField("Numero di telefono", validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder" : "Numero di telefono"})


class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Nome"}, id='name')
    surname = StringField('Cognome', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Cognome"})
    gender = SelectField('Genere', choices=[("", "--Seleziona un genere--"),("Male", "Male"),("Female", "Female"), ("Non Binary", "NonBinary"), ("Other", "Other")], validators=[DataRequired(message="Campo richiesto")])
    password = PasswordField('Password', validators=[DataRequired(message="Campo richiesto"), Length(min=8, message="La password deve essere lunga almeno 8 caratteri!")], render_kw={"placeholder":"Password"})
    repeat_password = PasswordField('Reinserisci Password', validators=[DataRequired(message="Campo richiesto"), EqualTo("password", message="Le password non corrispondo!")], render_kw={"placeholder":"Ripeti Password"})
    email = EmailField('Email', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Email"})
    repeat_email = EmailField('Reinserisci Email', validators=[DataRequired(message="Campo richiesto"), EqualTo('email', message='Le email devono corrispondere!')], render_kw={"placeholder":"Ripeti Email"})
    phone = StringField('Numero di Telefono', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Numero di Telefono"})
    address = StringField('Indirizzo', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Indirizzo"})
    birth_date = DateField('Data di Nascita', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data di Nascita"})
    student_city = StringField("Provincia di provenienza", validators=[DataRequired(message="Inserire provincia")], render_kw={"placeholder":"Provincia"})

    school_name = StringField('Nome scuola di provenienza', render_kw={"placeholder" : "Nome scuola"}, validators=[DataRequired(message="Campo Richiesto")])
    school_id = StringField(validators=[DataRequired(message="Campo Richiesto")])

    school_year = StringField('Anno scolastico', render_kw={"placeholder":"Anno scolastico"}, validators=[DataRequired(message="Campo richiesto")])

    def validate_repeat_password(self, password):
        
        if password.data != self.password.data:
            raise validators.ValidationError("Le password non corrispondono!")
            
    
    # def validate_email(self, email):

    #     if get_user_by_email(email.data) is not None:
    #         raise ValidationError("email già esistente!")
            #mandare un messaggio di errore alla mail che qualcuno ha provato ad accedere al proprio acccount?

    def validate_repeat_email(self, email):
        if email.data != self.email.data:
            raise validators.ValidationError("Le email non corrispondono!")

    def validate_password(self, password):
        throw_error = False

        (category, throw_error) = ("notpassed", True) if not self.check_password_length(password.data) else ("passed", throw_error)

        
        (category, throw_error) = ("notpassed", True) if not self.check_password_caps(password.data) else ("passed", throw_error)

        
        (category, throw_error) = ("notpassed", True) if not self.check_password_special(password.data) else ("passed", throw_error)
       
        (category, throw_error) = ("notpassed", True) if not self.check_password_number(password.data) else ("passed", throw_error)
         
        if throw_error == True:
            raise ValidationError("Inserisci una password valida!")

    def validate_phone(self, phone):
        phone_number = phone.data
        for c in phone_number: 
            if not c.isdigit():
                raise ValidationError("Inserisci un numero valido")

    def check_password_number(self, password):
        isNumber = False
        for number in password:
            if number.isdigit():
                isNumber = True
        return isNumber 

    def check_password_caps(self, password):
        isCaps = False
        for c in password:
            if c.isupper() == True:
                isCaps = True
        return isCaps

    def check_password_special(self, password):
        isSpecial = False
        for char in password:
            if char in ['@','_','-','*','$','%','&','+','£']:
                isSpecial = True
        return isSpecial

    def check_password_length(self, password):
        return len(password) >= 8

class LoginForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired(message="Devi inserire la mail per poter accedere!")], render_kw={"placeholder" : "email"})
    password = PasswordField('password', validators=[DataRequired(message="Devi inserire la password per poter accedere!")], render_kw={"placeholder" : "password"})
    remember_me = BooleanField("Remember me")

auth = Blueprint("auth_blueprint", __name__, template_folder='templates')

def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            elif not exists_role_user(current_user.get_id(), role_name):
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = create_user(form)
        result = add_user(new_user, form)
        if result == 'UniqueError':
            form.email.errors.append("Email già esistente!")
        elif result == True:
            return redirect(url_for("home"))
    
    return render_template("register.html", form=form, user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))
    

@auth.route('/register/professor', methods=['GET', 'POST'])
@role_required("Admin")
def register_professor():
    form = ProfessorRegisterForm()
    if form.validate_on_submit():
        import random
        import string
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(8))
        
        
        new_professor = create_user(form, password=password, is_student = False)
        result = add_user(new_professor, form, is_student=False)
        if result == 'UniqueError':
            form.email.errors.append("Email già esistente!")
        elif result == True:
            
            #manda email al prof
           
            flash("Il professore di riferimento ha ricevuto una mail di conferma contenente la password.")
            return redirect(f'/send_email?obj=Registrazione%20a%20DaisPCTO%21&recipient={form.email.data}&password={password}')

    return render_template("register.html", form = form, user = current_user,
                                            registration_prof = True,
                                            is_professor = True)       
                                            

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash("Sei già loggato!")
        return redirect(url_for("home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
    
        if user and compare_password(user.Password, form.password.data):
            login_user(user, remember=form.remember_me.data)
            next = request.args.get('next')
            return redirect(next or url_for("home"))
        else:
            form.email.errors.append("")
            form.password.errors.append("")
            flash("I campi inseriti non sono corretti")
            

    return render_template("login.html", form = form, user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))
        

@auth.route('/logout')
def logout():
    logout_user()
    return redirect(url_for("home"))


@auth.route('/test')
def test():
    extestone()
    return "ok"
    
