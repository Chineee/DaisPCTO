from flask_login import login_required, login_user, current_user, logout_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators, SelectMultipleField
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length
from flask import Blueprint, render_template, url_for, redirect, flash, abort, request
from DaisPCTO.models import *
from DaisPCTO.check import checkPasswordLength, checkPasswordCaps, checkPasswordSpecial, checkPasswordNumber
from DaisPCTO.db import *
from . import is_professor
from functools import wraps


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
    #cap = StringField("CAP", validators=[DataRequired(message="Inserire il CAP")])

    school_name = StringField('Nome scuola di provenienza', render_kw={"placeholder":"Nome scuola di provenienza"})
    school_city = StringField(u'Provincia scuola di provenienza', render_kw={"placeholder":"Città scuola di provenienza"}, )

    school_year = StringField('Anno scolastico', render_kw={"placeholder":"Anno scolastico"})

    def validate_repeat_password(self, password):
        
        if password.data != self.password.data:
            raise validators.ValidationError("Le password non corrispondono! Clicca qui per accedere!")
            
    
    def validate_email(self, email):

        if get_user_by_email(email.data) is not None:
            raise ValidationError("email già esistente!")
            #mandare un messaggio di errore alla mail che qualcuno ha provato ad accedere al proprio acccount?

    def validate_repeat_email(self, email):
        if email.data != self.email.data:
            raise validators.ValidationError("Le email non corrispondono!")

    def validate_password(form, password):
        throw_error = False

        (category, throw_error) = ("notpassed", True) if not checkPasswordLength(password.data) else ("passed", throw_error)

        flash("La password deve avere almeno 8 caratteri", category)
        
        (category, throw_error) = ("notpassed", True) if not checkPasswordCaps(password.data) else ("passed", throw_error)

        flash("La password deve contenere almeno un carattere maiuscolo", category)
        
        (category, throw_error) = ("notpassed", True) if not checkPasswordSpecial(password.data) else ("passed", throw_error)

        flash("La password deve contenere almeno un carattere speciale", category)
        
        (category, throw_error) = ("notpassed", True) if not checkPasswordNumber(password.data) else ("passed", throw_error)
        
        flash("La password deve contenere almeno un numero", category)
        
        if throw_error == True:
            raise ValidationError("Inserisci una password valida!")

    def validate_phone(self, phone):
        phone_number = phone.data
        for c in phone_number:
            if not c.isdigit():
                raise ValidationError("Inserisci un numero valido")
        

class LoginForm(FlaskForm):
    email = EmailField('email', validators=[DataRequired(message="Devi inserire la mail per poter accedere!")], render_kw={"placeholder" : "email"})
    password = PasswordField('password', validators=[DataRequired(message="Devi inserire la password per poter accedere!")], render_kw={"placeholder" : "password"})
    remember_me = BooleanField("Remember me")


    

auth = Blueprint("auth_blueprint", __name__, template_folder='templates')


# def professor_required(f):
#     @wraps(f)
#     def decorated_function(*args, **kwargs):
#         if not current_user.is_authenticated:
#             abort(401)
#         else:
#             if not current_user.hasRole("Professor"):
#                 abort(401)
#             else:
#                 return f(*args, **kwargs)
#     return decorated_function


def role_required(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            elif not current_user.hasRole(role_name):
                abort(401)
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = create_user(form)
        if add_user(new_user):
            return redirect(url_for("home"))
    
    return render_template("register.html", form=form, user=current_user, is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"))

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
    
