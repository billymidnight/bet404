import ast
import flask
import requests
from datetime import datetime
from trajanbet.models import get_db
from trajanbet import app
from flask import redirect, request, render_template

def convert_odds_to_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)
    
@app.route("/ev_finder", methods=["GET", "POST"])
def ev_finder():
    """
    Retrieves EV bets from the database with optional filters.
    """

    db = get_db()

    sportsbook = request.form.get("sportsbook", None)
    sport = request.form.get("sport", None)
    live_filter = request.form.get("live", None)

    query = "SELECT *, DATETIME(commence_time) as game_time FROM evbets"
    params = []

    if sportsbook and sportsbook != "allbooks":
        query += " WHERE book = ?"
        params.append(sportsbook)

    if sport and sport != "allsports":
        if params:
            query += " AND sport = ?"
        else:
            query += " WHERE sport = ?"
        params.append(sport)

    query += " ORDER BY ev DESC"
    ev_bets = db.execute(query, params).fetchall()

    current_time = datetime.now()
    filtered_bets = []
    for bet in ev_bets:
        game_time = datetime.strptime(bet["game_time"], "%Y-%m-%d %H:%M:%S")
        bet["live"] = "Live" if game_time <= current_time else "Upcoming"

        if live_filter == "nolive" and bet["live"] == "Live":
            continue
        if live_filter == "yeslive" and bet["live"] == "Upcoming":
            continue

        filtered_bets.append(bet)

    return render_template("evbets.html", ev_bets=filtered_bets)

    
@app.route('/ev_populate/', methods=['GET', 'POST'])
def ev_populate():
    """
    Populates the evbets table with expected value calculations for H2H markets,
    using vig-free (normalized) implied probabilities.
    """
    with open("allodds.txt", "r") as file:
        data = file.read()

    try:
        odds_data = ast.literal_eval(data)
    except Exception as e:
        print("Error parsing allodds.txt:", str(e))
        return

    db = get_db()
    db.execute("DELETE FROM evbets")

    for sport, games in odds_data.items():
        for game in games:
            hometeam = game["home_team"]
            awayteam = game["away_team"]
            commence_time = datetime.strptime(game["commence_time"], "%Y-%m-%dT%H:%M:%SZ")

            all_bookmakers = game["bookmakers"]
            outcome_probs = {}

            # Build vig-free probabilities
            for bookmaker in all_bookmakers:
                for market in bookmaker["markets"]:
                    if market["key"] != "h2h":
                        continue

                    implied_probs = []
                    team_names = []

                    for outcome in market["outcomes"]:
                        team = outcome["name"]
                        odds = int(outcome["price"])
                        implied_prob = convert_odds_to_probability(odds)
                        implied_probs.append(implied_prob)
                        team_names.append(team)

                    book = sum(implied_probs)

                    for i, team in enumerate(team_names):
                        vig_free_prob = implied_probs[i] / book
                        if team not in outcome_probs:
                            outcome_probs[team] = []
                        outcome_probs[team].append(vig_free_prob)

            avg_implied_probs = {
                team: sum(probs) / len(probs) for team, probs in outcome_probs.items()
            }

            for bookmaker in all_bookmakers:
                book_name = bookmaker["title"]
                for market in bookmaker["markets"]:
                    if market["key"] != "h2h":
                        continue

                    for outcome in market["outcomes"]:
                        team = outcome["name"]
                        odds = int(outcome["price"])
                        implied_prob = convert_odds_to_probability(odds)
                        avg_prob = avg_implied_probs.get(team, 0)

                        possible_win = odds if odds > 0 else (100 / -odds) * 100
                        ev = (avg_prob * possible_win) + ((1 - avg_prob) * -100)

                        db.execute(
                            """
                            INSERT INTO evbets (ev, sport, outcome, outcome_odds, book, 
                                                implied_prob, avg_implied_prob, commence_time, 
                                                hometeam, awayteam)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """,
                            (
                                round(ev, 2), sport, team, odds, book_name,
                                round(implied_prob, 5), round(avg_prob, 5), commence_time,
                                hometeam, awayteam
                            )
                        )

    db.commit()
    print("EV Bets table populated successfully.")
    return flask.render_template('menu.html')
