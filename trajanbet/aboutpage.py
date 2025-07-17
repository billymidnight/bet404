import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime
from trajanbet.arbitrage import arbpopulator



@app.route("/aboutpage", methods=["GET"])
def aboutpage():
    return flask.render_template("aboutpage.html")
