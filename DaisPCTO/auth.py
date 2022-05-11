from flask import flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SelectField, DateField, BooleanField, SubmitField, validators
from wtforms.validators import DataRequired, EqualTo
from flask import Blueprint, render_template
from DaisPCTO.models import *
from DaisPCTO.check import checkPasswordLength, checkPasswordCaps, checkPasswordSpecial, checkPasswordNumber
from DaisPCTO.db import *


class RegisterForm(FlaskForm):
    name = StringField('Nome', validators=[DataRequired()], render_kw={"placeholder":"Nome"}, id = "sos")
    surname = StringField('Cognome', validators=[DataRequired()], render_kw={"placeholder":"Cognome"})
    gender = SelectField('Genere', choices=[("", "--Seleziona un genere--"),("Male", "Male"),("Female", "Female"), ("Non Binary", "NonBinary"), ("Other", "Other")], validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()], render_kw={"placeholder":"Password"})
    repeatPassword = PasswordField('Reinserisci Password', validators=[DataRequired()], render_kw={"placeholder":"Ripeti Password"})
    email = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder":"Email"})
    repeatEmail = EmailField('Reinserisci Email', validators=[DataRequired(), EqualTo('email', message='Le email devono corrispondere goldon')], render_kw={"placeholder":"Ripeti Email"})
    phone = StringField('Numero di Telefono', validators=[DataRequired()], render_kw={"placeholder":"Numero di Telefono"})
    address = StringField('Indirizzo', validators=[DataRequired()], render_kw={"placeholder":"Indirizzo"})
    birthDate = DateField('Data di Nascita', validators=[DataRequired()], render_kw={"placeholder":"Data di Nascita"})

    schoolName = StringField('Nome scuola di provenienza', render_kw={"placeholder":"Nome scuola di provenienza"})
    schoolCity = StringField(u'Città scuola di provenienza', render_kw={"placeholder":"Città scuola di provenienza"}, )

    schoolYear = StringField('Anno scolastico', render_kw={"placeholder":"Anno scolastico"})

    submit = SubmitField("Sign-Up")

    def validate_repeatPassword(self, password):
        if password.data != self.password.data:
            raise validators.ValidationError("Le password non corrispondono!")
            
            
    def validate_repeatEmail(self, email):
        if email.data != self.email.data:
            raise validators.ValidationError("Le email non corrispondono!")
            
            
    def validate_password(self, password):
        pass
        # if (password.data != self.password.data):
        #     raise validators.ValidationError("Le password devono corrispondere!")
        
        # if not checkPasswordLength(password.data):
        #     raise validators.ValidationError("La password deve avere almeno 8 caratteri")
        
        # if not checkPasswordCaps(password.data):
        #     raise validators.ValidationError("La password deve contenere almeno un carattere maiuscolo")
        
        # if not checkPasswordSpecial(password.data):
        #     raise validators.ValidationError("La password deve contenere almeno un carattere speciale")
        
        # if not checkPasswordNumber(password.data):
        #      raise validators.ValidationError("La password deve contenere almeno un numero") 

            


class Login(FlaskForm):
    email = StringField('email', validators=[DataRequired()])
    password = PasswordField('password', validators=[DataRequired()])
    remberMe = BooleanField("rememberme")
    submit = SubmitField("Log-In")

auth = Blueprint("auth_blueprint", __name__, template_folder='templates')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = create_user(form)
        if add_user(new_user):
            return "ciaone"
        else:
            return render_template("register.html", user_error=True)

    else:
        return render_template("register.html", form=form)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    pass





    
    

    
