from flask import Flask, render_template, request, redirect, url_for
from trajanbet import app
from trajanbet.models import get_db
import datetime
from datetime import datetime
from math import gcd
import requests
import json
from config import ODDS_API_KEY


@app.route("/endrace/<int:race_id>", methods=["GET"])
def endrace(race_id):
    """
    Displays a form to manually enter the race results, allowing the user to assign finishing positions.
    """
    db = get_db()

    # Fetch race details
    race = db.execute(
        "SELECT * FROM races WHERE raceid = ?", (race_id,)
    ).fetchone()

    if not race:
        return "Race not found", 404

    # Get horses for the race
    horses = db.execute(
        "SELECT * FROM horses WHERE raceid = ?", (race_id,)
    ).fetchall()

    return render_template("endrace.html", race=race, horses=horses)

@app.route("/finishrace", methods=["GET", "POST"])
def finishrace():
    """
    Completes the race, updates standings, and settles bets.
    Redirects to donerace.html with final results.
    """
    race_id = request.args.get("race_id")
    if not race_id:
        return "Race ID is missing", 400

    db = get_db()

    if request.method == "POST":
        db.execute("UPDATE races SET completed = 1 WHERE raceid = ?", (race_id,))

        standings = []
        first_place_horse_id = None
        position = 1

        while f"position_{position}" in request.form:
            horse_id = request.form.get(f"position_{position}")
            if not horse_id:
                continue

            db.execute(
                "UPDATE horses SET position_finished = ? WHERE horseid = ?",
                (position, horse_id),
            )

            if position == 1:
                first_place_horse_id = horse_id

            horse_info = db.execute(
                "SELECT horsename FROM horses WHERE horseid = ?", (horse_id,)
            ).fetchone()

            if horse_info:
                standings.append({
                    "position": position,
                    "horsename": horse_info["horsename"],
                    "horseid": horse_id
                })

            position += 1

    else:  
        standings = db.execute(
            """
            SELECT h.horsename, h.horseid, h.position_finished as position 
            FROM horses h 
            WHERE h.raceid = ? 
            ORDER BY h.position_finished ASC
            """,
            (race_id,),
        ).fetchall()

        first_place_horse_id = standings[0]["horseid"] if standings else None



    winning_bettors = []
    bet_history = []
    losingsum = 0
    winningsum = 0

    bets = db.execute(
        "SELECT b.bettorname, b.horseid, b.betamount, b.time_placed, h.horsename "
        "FROM racebets b "
        "JOIN horses h ON b.horseid = h.horseid WHERE h.raceid = ?",
        (race_id,),
    ).fetchall()

    for bet in bets:
        is_winner = (int(bet["horseid"]) == int(first_place_horse_id))
        result = "Win" if is_winner else "Loss"

        if is_winner:
            winning_bettors.append(bet["bettorname"])
            winningsum += int(bet["betamount"])
        else:
            losingsum += int(bet["betamount"])

        try:
            formatted_time = datetime.strptime(bet["time_placed"], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %Y %I:%M %p")
        except ValueError:
            formatted_time = bet["time_placed"] 

        bet_history.append({
            "bettorname": bet["bettorname"],
            "horsename": bet["horsename"],
            "horseid": bet["horseid"],
            "betamount": bet["betamount"],
            "time_placed": formatted_time,
            "result": result
        })

    for bet in bet_history:
        is_winner = (int(bet["horseid"]) == int(first_place_horse_id))
        bet["winnings"] = round((int(bet["betamount"]) / winningsum) * losingsum, 2) if is_winner else 0
        bet["payout"] = round(bet["winnings"] + int(bet["betamount"]), 2) if is_winner else 0

    db.execute(
        """
        UPDATE racebets 
        SET active_or_settled = 'settled' 
        WHERE horseid IN (SELECT horseid FROM horses WHERE raceid = ?)
        """,
        (race_id,),
    )

    db.commit()

    return render_template(
        "donerace.html",
        race_id=race_id,
        standings=standings,
        bet_history=bet_history,
        winning_bettors=winning_bettors,
    )

@app.route("/checksettles/", methods=["GET", "POST"])
def checksettles():

    api_key = ODDS_API_KEY
    db = get_db()

    unsettled_races = db.execute(
        "SELECT raceid, event_id, sport_key FROM races WHERE type = 'real' AND completed = 0"
    ).fetchall()

    if not unsettled_races:
        return "No unsettled races found."
    
    event_ids = [race["event_id"] for race in unsettled_races]
    sport_keys = list(set(race["sport_key"] for race in unsettled_races))

    print(sport_keys, " were thge sport_keys and these were the event_ids ", event_ids)
    url = f"https://api.the-odds-api.com/v4/sports/{sport_keys[0]}/scores/?apiKey={api_key}&eventIds={','.join(event_ids)}&daysFrom=3"

    response = requests.get(url)
    if response.status_code != 200:
        return "Error fetching scores from API."

    scores_data = response.json()

    # Save API response to a text file for debugging
    with open("scores.txt", "w") as file:
        json.dump(scores_data, file, indent=4)

    for game in scores_data:
        if not game["completed"]:
            continue  # Skip if the game isn't finished yet

        event_id = game["id"]
        home_team = game["home_team"]
        away_team = game["away_team"]
        home_score = int(game["scores"][0]["score"])
        away_score = int(game["scores"][1]["score"])

        # Determine winner
        if home_score > away_score:
            winner = home_team
        elif home_score < away_score:
            winner = away_team
        else:
            winner = "Draw"

        # Mark race as completed
        db.execute(
            "UPDATE races SET completed = 1, home_score = ?, away_score = ? WHERE event_id = ?",
            (home_score, away_score, event_id),
        )

        print(f"winner of this race was {winner}")

        # Update horses table - Set winner to 1, others to 0
        db.execute(
            "UPDATE horses SET position_finished = 1 WHERE raceid = (SELECT raceid FROM races WHERE event_id = ?) AND horsename = ?",
            (event_id, winner),
        )
        db.execute(
            "UPDATE horses SET position_finished = 0 WHERE raceid = (SELECT raceid FROM races WHERE event_id = ?) AND horsename != ?",
            (event_id, winner),
        )

        # Mark all bets as settled
        db.execute(
            """
            UPDATE racebets
            SET active_or_settled = 'settled'
            WHERE horseid IN (
                SELECT horseid FROM horses WHERE raceid = (SELECT raceid FROM races WHERE event_id = ?)
            )
            """,
            (event_id,),
        )

    db.commit()

    return render_template("races.html")

    