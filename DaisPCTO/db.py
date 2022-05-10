
#qua definire engine e sessione che verrà usata usando funzione sessionmaker(bind=engine). Ogni volta che si manipola il database, creare una nuova sessione usando la funzione session().

#! Usare try catch statement per verificare se l'inserimento può essere effettuato. Se il commit fallisce, fare una rollback per quella sessione.

from sqlalchemy.orm import *
from sqlalchemy import *

engine = create_engine("postgresql://postgres:123456@localhost/testone2", echo=True) #!teniamo true echo solo per puro debugging, quando avremo finito settiamolo a false per anche velocizzare l'app dato che le print sono molto pesanti
Session = sessionmaker(bind=engine)

def create_user(obj_formed):
    pass

def add_database(user):
    try:
        pass 
    except:
        pass

