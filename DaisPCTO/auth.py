from flask import Blueprint
from flask_login import *
from flask_wtf import *
from DaisPCTO.db import add_database

auth = Blueprint("auth", __name__)

class LoginForm(FlaskForm):
    pass 

class RegisterForm(FlaskForm):
    pass

@auth.route("/register")
def register():
    pass 

@auth.route("/login")
def login():
    return "hello login"