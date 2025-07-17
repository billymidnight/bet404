import flask
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 

@app.route('/freebet/', methods=["GET"])
def free_bet_shower():
    con = get_db()
    con.row_factory = sqlite3.Row 

    cur = con.execute("SELECT * FROM default_freebet")
    placeholder_data = cur.fetchone()

    # Explicitly add placeholders
    context = {
        "game": placeholder_data["game"],
        "line": placeholder_data["line"],
        "udogodds": placeholder_data["udogodds"],  
        "favsodds": placeholder_data["favsodds"],  
        "betamount": placeholder_data["betamount"],  
        "freebetbook": "",  # Optional field
        "realmoneybook": "",  # Optional field
        "real_money_bet_amount": 195.01,
        "hedge_value": 0.65,
        "exact_winnings": 65,
    }

    return flask.render_template('freebet.html', **context)


@app.route('/free_bet_calc', methods=["POST"])
def free_bet_calc():
    game = request.form["game"]
    udog_odds = int(request.form["udogodds"])
    favs_odds = int(request.form["favsodds"])
    bet_amount = float(request.form["betamount"])
    line = request.form.get("line", "Some Line")
    freebet_book = request.form.get("freebetbook", "Some Book")
    realmoney_book = request.form.get("realmoneybook", "Some Book")

    try:
        y = ((udog_odds / 100) * bet_amount) / ((100 / (-favs_odds)) + 1)
        winnings = bet_amount * (udog_odds / 100) - y
        hedge_val = winnings / bet_amount
    except ZeroDivisionError:
        y = 0
        winnings = 0
        hedge_val = 0

    context = {
        "udogodds": udog_odds,
        "favsodds": favs_odds,
        "betamount": bet_amount,
        "game": game,
        "line": line,
        "freebetbook": freebet_book,
        "realmoneybook": realmoney_book,
        "real_money_bet_amount": round(y, 2),
        "exact_winnings": round(winnings, 2),
        "hedge_value": round(hedge_val, 2)
    }
    return flask.render_template("freebet.html", **context)
