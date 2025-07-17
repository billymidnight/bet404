from flask import Flask, render_template, request, redirect, url_for
from trajanbet import app
from trajanbet.models import get_db
import datetime
from datetime import datetime
from math import gcd

def simplify_odds(a, b):
    if a == 0 or b == 0:
        return "-", None, None 

    divisor = gcd(int(a), int(b))
    simplified_a = int(a // divisor)
    simplified_b = int(b // divisor)


    return f"{simplified_a} to {simplified_b}", simplified_a, simplified_b

@app.route("/parimutuel")
def parimutuel():
    return render_template("parimutuel.html")

@app.route("/races")
def races():
    return render_template("races.html")

import sqlite3
from flask import request, render_template, redirect, url_for
from trajanbet import app
from trajanbet.models import get_db

@app.route("/createrace/", methods=["GET"])
def createrace():
    return render_template("createrace.html")

@app.route("/racecreator", methods=["POST"])
def racecreator():
    """
    Handles the creation of a new race by storing race and horse details in the database.
    Redirects to the individual race page after successful creation.
    """

    race_name = request.form.get("race_name")
    race_venue = request.form.get("race_venue")
    num_participants = int(request.form.get("num_participants"))

    if not race_name or not race_venue or num_participants < 2:
        return "Invalid race details", 400

    db = get_db()

    cursor = db.execute(
        "INSERT INTO races (racename, racevenue, completed) VALUES (?, ?, ?)",
        (race_name, race_venue, 0),
    )
    race_id = cursor.lastrowid  

    horse_names = []
    for i in range(1, num_participants + 1):
        horse_name = request.form.get(f"horse_{i}")
        if horse_name:
            horse_names.append(horse_name)
            db.execute(
                "INSERT INTO horses (horsename, raceid, position_finished) VALUES (?, ?, ?)",
                (horse_name, race_id, None),  
            )

    db.commit()

    # Redirect to the newly created race page
    return redirect(url_for("onerace", race_id=race_id))

@app.route("/raceviewer", methods=["GET"])
def raceviewer():
    """Displays all active and completed races with details on horses and prize pools."""

    db = get_db()

    races = db.execute("SELECT * FROM races ORDER BY raceid DESC").fetchall()

    race_details = []
    for race in races:
        race_id = race["raceid"]

        horse_count = db.execute(
            "SELECT COUNT(*) as count FROM horses WHERE raceid = ?", (race_id,)
        ).fetchone()["count"]

        total_pool = db.execute(
            "SELECT SUM(betamount) as total FROM racebets JOIN horses on racebets.horseid = horses.horseid WHERE raceid = ?", (race_id,)
        ).fetchone()["total"]

        if total_pool is None:
            total_pool = 0

        race_details.append({
            "raceid": race_id,
            "racename": race["racename"],
            "racevenue": race["racevenue"],
            "completed": race["completed"],
            "horse_count": horse_count,
            "prize_pool": total_pool
        })

    active_races = [race for race in race_details if race["completed"] == 0]
    completed_races = [race for race in race_details if race["completed"] == 1]

    return render_template(
        "allraces.html",
        active_races=active_races,
        completed_races=completed_races
    )

@app.route("/onerace/<int:race_id>", methods=["GET"])
def onerace(race_id):
    """ Fetches race details, horses, bets, implied odds, and calculates potential winnings. """

    db = get_db()

    race = db.execute(
        "SELECT * FROM races WHERE raceid = ?", (race_id,)
    ).fetchone()

    if not race:
        return "Race not found", 404

    horses = db.execute(
        "SELECT * FROM horses WHERE raceid = ?", (race_id,)
    ).fetchall()

    bets = db.execute(
        """
        SELECT b.*, h.horsename FROM racebets b
        JOIN horses h ON b.horseid = h.horseid
        WHERE h.raceid = ?
        ORDER BY betid DESC
        """,
        (race_id,),
    ).fetchall()

    total_bets = {horse["horsename"]: 0 for horse in horses}
    total_pool = 0

    for bet in bets:
        total_bets[bet["horsename"]] += bet["betamount"]
        total_pool += bet["betamount"]

    implied_odds = {}
    odds_ratios = {}
    bookie_probs = []

    raw_probs = []  # Store raw implied probabilities before normalization

    for horse in horses:
        horse_name = horse["horsename"]
        horse_total_bets = total_bets[horse_name]

        if horse_total_bets > 0:
            odds_text, num, denom = simplify_odds(total_pool - horse_total_bets, horse_total_bets)
            implied_odds[horse_name] = odds_text
            odds_ratios[horse_name] = (num, denom)
        else:
            implied_odds[horse_name] = "-"
            odds_ratios[horse_name] = (None, None)

        if race["type"] == "real":
            opening_odds = horse.get("opening_odds", 0)
            if opening_odds > 0:
                prob = 100 / (opening_odds + 100)
            else:
                prob = -opening_odds / (-opening_odds + 100)
            prob = round(prob, 2)
            raw_probs.append(prob)  

    total_prob = sum(raw_probs)
    if total_prob > 0:
        bookie_probs = [(p / total_prob) * 100 for p in raw_probs]
        bookie_probs = [round(p, 2) for p in bookie_probs] 

    bet_history = []
    for bet in bets:
        bettor_name = bet["bettorname"]
        horse_name = bet["horsename"]
        bet_amount = bet["betamount"]
        time_placed = bet["time_placed"]

        num, denom = odds_ratios[horse_name]
        if num is not None and denom is not None and num > 0:
            possible_winnings = round(bet_amount * (num / denom), 2)
        else:
            possible_winnings = 0.00

        bet_history.append({
            "bettorname": bettor_name,
            "horsename": horse_name,
            "betamount": bet_amount,
            "time_placed": time_placed,
            "winnings": possible_winnings
        })
    
    commence_time_js = race["commence_time"]
    return render_template(
        "onerace.html",
        race=race,
        commence_time_js=commence_time_js,
        total_pool=total_pool,
        horses=horses,
        total_bets=total_bets,
        implied_odds=implied_odds,
        bet_history=bet_history,
        realorcustom=race["type"],
        bookie_odds=bookie_probs if race["type"] == "real" else None
    )


@app.route("/newbet", methods=["POST"])
def newbet():
    """Handles new bet placements and updates the racebets table."""
    race_id = request.args.get("race_id")
    bettor_name = request.form.get("bettorname")
    horse_id = request.form.get("horseid")
    bet_amount = request.form.get("betamount")
    print(race_id, bettor_name, horse_id, bet_amount)
    if not (race_id and bettor_name and horse_id and bet_amount):
        return "Missing information", 400

    db = get_db()

    db.execute(
        """
        INSERT INTO racebets (bettorname, horseid, betamount, time_placed, active_or_settled)
        VALUES (?, ?, ?, ?, ?)
        """,
        (bettor_name, horse_id, float(bet_amount), datetime.now(), "active"),
    )
    db.commit()

    return redirect(url_for("onerace", race_id=race_id))