import os
import flask
from trajanbet import app  
from trajanbet.models import get_db

@app.route('/', methods=['GET'])
def mainmenu():
    return flask.render_template("menu.html")
