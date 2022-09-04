from flask import Flask, render_template, session as flasksession, redirect, url_for, request, flash
from flask_login import current_user, LoginManager
from DaisPCTO.auth import role_required
from DaisPCTO.db import get_student_certificates, compare_password, get_users_role, update_user_psw, get_student_courses, get_user_by_id, get_schools_with_name, get_student_by_user, get_school_by_id
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect, CSRFError
from flask.json import jsonify
from flask_gravatar import Gravatar
from flask_mail import Mail, Message
import base64 
import io
import qrcode
import json

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = "mysecretkey"
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_USERNAME'] = "daispcto@gmail.com"
    app.config['MAIL_PASSWORD'] = "dbnmksyoukdicynn"
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True

    csrf = CSRFProtect()
    csrf.init_app(app)
    Bootstrap(app)
    mail = Mail(app)
    login_manager = LoginManager()
    login_manager.login_view = "auth_blueprint.login"
    login_manager.init_app(app)
    login_manager.login_message = "Devi accedere per poter visitare questa pagina!"

    """
    Send email viene richiamata solo dall'admin quando aggiunge un nuovo professore al database. Al professore in questione verrà inviata una mail con
    tutti i dati necessari all'accesso alla webapp
    """
    @app.route("/send_email")
    @role_required("Admin")
    def send_email():
        msg = Message(
            request.args.get("obj"),
            sender="daispcto@gmail.com",
            recipients = [request.args.get("recipient")]
        )
        msg.body = f"Gentile utente, \n\
        sei stato registrato con successo al sito DaisPCTO! \n\n\
        La password per accedere è la seguente:{request.args.get('password')} \n\
        Cambiala al più presto! \n\n\
        Buona Giornata!"

        mail.send(msg)
        return redirect(url_for("home"))

    gravatar = Gravatar(app,
                    size=100,
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)

    """
    Questa route viene richiamata da Ajax per ottenere le scuole disponibili per gli utenti in fase di registrazione, il suo unico scopo è quello di migliorare
    l'aspetto grafico della webapp durante la registrazione, presentando un form con una lista delle scuole disponibili, con una funzione di ricerca
    intuibile all'utente.
    """
    @app.route('/action/get/schools')
    def give_school_attribute():
        
        name = request.args.get("name") #In questo caso l'utente inserisce il nome della scuola, ed il server restituisce tutte le scuole contenenti quel nome
        if name == "":
            return jsonify({"success" : False})
        l = get_schools_with_name(name.upper())

        res = []

        for school in l:
            school_add = {}
            school_add["School_id"] = school.SchoolID
            school_add["School_name"] = school.SchoolName
            school_add["School_city"] = school.City
            school_add["School_region"] = school.Region
            school_add["School_address"] = school.Address
         
            res.append(school_add)
    
        return jsonify({"success" : True, "result" : res})

    """
    Il concetto è identico a quello per le scuole, solo che si utilizzano le province, e non vengono prese dal database, ma da un file json salvato in locale
    """
    @app.route('/action/get/province')
    def give_province():
        with open("province.json") as f:
            data = json.load(f)
            res = []

            name = request.args.get("name").upper()
            if (len(name) == 0):
                 return jsonify({"success" : False})
            
            for city in data:
                if city['nome'].upper().startswith(name):
                    city_add = {}
                    city_add['nome'] = city['nome'].upper()
                    city_add['sigla'] = city['sigla'].upper()
                    city_add['regione'] = city['regione'].upper()
                    res.append(city_add)
            
            return jsonify({"success" : True, "result" : res})

    """
    Homepage della webapp, l'azione di post viene usata in caso l'utente voglia cambiare la password.
    In caso di utente anonimo o non loggato, la pagina sarà vuota. In caso di utente autenticato, la pagina mostrerà gravatar dell'utente insieme
    ad alcune sue informazioni generali, come mail, scuola di provenienza in caso di studente e ruolo dell'utente.
    """

    @app.route("/", methods=['GET', 'POST'])
    def home():    
        if request.method == 'POST':
            old_psw = request.form['oldpassword']   
            if compare_password(current_user.Password, old_psw):
                new_psw = request.form['newpassword']
                new_psw_2 = request.form['newpassword2']
                if len(new_psw) >= 8 and new_psw == new_psw_2:
                    control = [False, False, False]
                    for c in new_psw:
                        if c.isupper():
                            control[0] = True 
                        elif c.isdigit():
                            control[1] = True 
                        elif c in ['@','_','-','*','$','%','&','+','£']:
                            control[2] = True 
                    if control[0] and control[1] and control[2]:
                        update_user_psw(current_user.get_id(), new_psw)
    
        return render_template("page.html", user=current_user, 
                                            is_professor = False if not current_user.is_authenticated else current_user.hasRole("Professor"),
                                            is_student = False if not current_user.is_authenticated else current_user.hasRole("Student"),
                                            is_qr = False if not current_user.is_authenticated else current_user.hasRole("QrReader"),
                                            roles = get_users_role(current_user.get_id()))    

    @login_manager.user_loader
    def load_user(UserID):   
        return get_user_by_id(UserID, flask_request=True)

    @app.errorhandler(404)
    def page_not_found(e):
        return "err", 404

    """
    Ogni volta che il client proverà a fare una richiesta di tipo POST, il server richiederà un codice CSRF, che se non dato o se errato manderà un errore 400.
    Il CSRF Token può essere mandato o tramite header o tramite form
    """
    @app.before_request
    def check_csrf():
        csrf.protect()

    @app.template_filter("to_minutes")
    def to_minutes(time):
        return time.total_seconds()/60

    """
    Banale funzione per semplificare l'ottenimento di informazioni degli studenti
    """
    @app.template_filter("get_student_info")
    def get_student_info(user):
        s = get_student_by_user(user.UserID)
        if s is not None:
            school_name = get_school_by_id(s.SchoolID).SchoolName
            return (s.birthDate.strftime("%d-%m-%Y"), school_name, s.City)

    """
    Filter usato nella pagina de "I miei corsi" per gli studenti, ed ottenere una progress bar per indicare quanto manca all'ottenimento dell'attestato
    di partecipazione
    """
    @app.template_filter("get_completed_percentage")
    def get_completed_percentage(user_minutes, needed_hour):
        if needed_hour == 0:
            return 100
        perc = ( user_minutes/(needed_hour*60) ) * 100
        return perc if perc <= 100 else 100

    @app.template_filter("convert_to_integer")
    def convert_to_integer(number):
        #a quanto pare jinja non permette la conversione da str a int kekw
        return int(number)

    @app.template_filter("can_be_booked")
    def can_be_booked(lesson, number_reservation_for_each_lesson):
        '''
        data una lezione frontale, controlliamo il numero di studenti che hanno prenotato il posto in aula per questa, se supera o è uguale al numero di posti disponibili
        ritorniamo false. Questo valore viene controllato da jinja, e si comporta in modo diverso a seconda della risposta:
        False : Il bottone per prenotarsi sarà disattivato e non potrà essere premuto.
        True : Nessun cambiamento.

        NB che questi sono controlli solo per la parte front-end e non backend. I controlli "veri" per verificare se uno studente può o meno prenotarsi ad una lezione
        vengono effettuati tramite trigger di postgresql una volta che l'utente corrente ha fatto la richiesta.
        '''
    
        for booked in number_reservation_for_each_lesson:
            if booked.LessonID == lesson.LessonID:
                if booked.Reserv >= booked.Seats:
                    return (False, booked.Reserv)
                return (True, booked.Reserv)

    app.register_error_handler(404, page_not_found)

    from DaisPCTO.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from DaisPCTO.courses import courses as courses_blueprint 
    app.register_blueprint(courses_blueprint, url_prefix="/courses")

    from DaisPCTO.lessons import lessons as lessons_blueprint 
    app.register_blueprint(lessons_blueprint)

    from DaisPCTO.feedback import feedback as feedback_blueprint
    app.register_blueprint(feedback_blueprint)

    from DaisPCTO.qna import QnA as qna_blueprint 
    app.register_blueprint(qna_blueprint)
    
    return app