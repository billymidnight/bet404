import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime
from trajanbet.arbitrage import arbpopulator


@app.route("/arbfinder/", methods=["GET", "POST"])
def arbfinder():
    db = get_db()
    
    sportsbook = flask.request.form.get("sportsbook", None)
    sport = flask.request.form.get("sport", None)
    live_filter = flask.request.form.get("live", None)
    
    query = "SELECT *, DATETIME(commence_time) as game_time FROM arb_lines WHERE favs_book != 'Bovada'"
    params = []
    
    if sportsbook and sportsbook != "allbooks":
        query += " AND udogs_book = ?"
        params.append(sportsbook)
    
    if sport and sport != "allsports":
        query += " AND sport = ?"
        params.append(sport)
    
    query += " ORDER BY arb_margin DESC"
    lines = db.execute(query, params).fetchall()
    
    current_time = datetime.now()
    filtered_lines = []
    for line in lines:
        game_time = datetime.strptime(line["game_time"], "%Y-%m-%d %H:%M:%S")
        if game_time <= current_time:
            line["live"] = "Live"
        else:
            line["live"] = "Upcoming"
        
        if live_filter == "nolive" and line["live"] == "Live":
            continue
        if live_filter == "yeslive" and line["live"] == "Upcoming":
            continue
        
        filtered_lines.append(line)
    
    return flask.render_template("arbfinder.html", lines=filtered_lines)