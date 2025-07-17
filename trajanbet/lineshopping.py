import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request
from config import ODDS_API_KEY
import ast


@app.route("/lineshopping", methods=["GET", "POST"])
def lineshopping():
    """
    Displays all sports from the API and saves them in the sports table.
    Handles search functionality for filtering sports.
    """
    api_key = ODDS_API_KEY
    db = get_db()

    # If no search is performed, fetch data from the API and populate the sports table
    if not request.form.get("searchkey"):
        response = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}")
        if response.status_code == 200:
            sports_data = response.json()
            # Clear and populate sports table
            db.execute("DELETE FROM sports")
            for sport in sports_data:
                db.execute(
                    """
                    INSERT INTO sports (key, title, description, active, has_outright)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        sport["key"],
                        sport["title"],
                        sport["description"],
                        sport["active"],
                        sport["has_outrights"],
                    ),
                )
            db.commit()

    # Search functionality
    searchkey = request.form.get("searchkey", "").strip().lower()
    if searchkey:
        query = "SELECT key, title, description, active FROM sports WHERE LOWER(title) LIKE ? OR LOWER(description) LIKE ? ORDER BY title ASC"
        params = (f"%{searchkey}%", f"%{searchkey}%")
    else:
        query = "SELECT key, title, description, active FROM sports ORDER BY title ASC"
        params = ()

    sports = db.execute(query, params).fetchall()
    return flask.render_template("lineshopping.html", sports=sports)
