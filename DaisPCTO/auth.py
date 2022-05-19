from flask_login import login_required, login_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, EqualTo, ValidationError, Length
from flask import Blueprint, render_template, url_for, redirect, flash
from DaisPCTO.models import *
from DaisPCTO.check import checkPasswordLength, checkPasswordCaps, checkPasswordSpecial, checkPasswordNumber
from DaisPCTO.db import *


class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Nome"}, id='name')
    surname = StringField('Cognome', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Cognome"})
    gender = SelectField('Genere', choices=[("", "--Seleziona un genere--"),("Male", "Male"),("Female", "Female"), ("Non Binary", "NonBinary"), ("Other", "Other")], validators=[DataRequired(message="Campo richiesto")])
    password = PasswordField('Password', validators=[DataRequired(message="Campo richiesto"), Length(min=8)], render_kw={"placeholder":"Password"})
    repeatPassword = PasswordField('Reinserisci Password', validators=[DataRequired(message="Campo richiesto"), EqualTo("password", message="Le password non corrispondo!")], render_kw={"placeholder":"Ripeti Password"})
    email = EmailField('Email', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Email"})
    repeatEmail = EmailField('Reinserisci Email', validators=[DataRequired(message="Campo richiesto"), EqualTo('email', message='Le email devono corrispondere!')], render_kw={"placeholder":"Ripeti Email"})
    phone = StringField('Numero di Telefono', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Numero di Telefono"})
    address = StringField('Indirizzo', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Indirizzo"})
    birthDate = DateField('Data di Nascita', validators=[DataRequired(message="Campo richiesto")], render_kw={"placeholder":"Data di Nascita"})

    schoolName = StringField('Nome scuola di provenienza', render_kw={"placeholder":"Nome scuola di provenienza"})
    schoolCity = StringField(u'Città scuola di provenienza', render_kw={"placeholder":"Città scuola di provenienza"}, )

    schoolYear = StringField('Anno scolastico', render_kw={"placeholder":"Anno scolastico"})

    def validate_repeatPassword(self, password):
        if password.data != self.password.data:
            raise validators.ValidationError("Le password non corrispondono! Clicca qui per accedere!")
            
    
    def validate_email(self, email):
        if get_user_by_email(email.data) is not None:
            raise ValidationError("email già esistente!")
            #mandare un messaggio di errore alla mail che qualcuno ha provato ad accedere al proprio acccount?

    def validate_repeatEmail(self, email):
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
        

class LoginForm(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remberMe = BooleanField("Remember me")
    submit = SubmitField("Log-In")

auth = Blueprint("auth_blueprint", __name__, template_folder='templates')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = create_user(form)
        if add_user(new_user):
            return redirect(url_for("home"))
        else:
            return render_template("register.html", form=form, user=current_user)
    else:
        return render_template("register.html", form=form, user=current_user)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    pass


    

    
