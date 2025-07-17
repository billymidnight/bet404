import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime
from trajanbet.arbitrage import arbpopulator


@app.route("/laypopulator/", methods=["GET", "POST"])
def laypopulator():
    """
    Populates the all_lines table in the database with lay data.
    """
    sports = ["americanfootball_nfl", "basketball_nba", "americanfootball_ncaaf", "basketball_ncaab", "icehockey_nhl"]
    db = get_db()

    # Load all odds data from the local file
    with open("allodds.txt", "r") as file:
        data = file.read()

    odds_data = ast.literal_eval(data)  # Convert string back to a dictionary

    for sport, games in odds_data.items():
        for game in games:
            gametime = game["commence_time"]
            formatted_time = datetime.strptime(gametime, "%Y-%m-%dT%H:%M:%SZ")
            hometeam = game["home_team"]
            awayteam = game["away_team"]
            curr_sport = game["sport_key"]
            all_bookmakers = game['bookmakers']

            for bookmaker in all_bookmakers:
                curr_bookmaker_key = bookmaker["key"]
                print("Outer bookmaker:", curr_bookmaker_key)

                for market in bookmaker["markets"]:
                    outer_market = market["key"]

                    if outer_market != "h2h": 
                        continue

                    for outcome in market["outcomes"]:
                        curr_outcome = outcome["name"]
                        curr_odds = outcome["price"]

                        for inner_bookmaker in all_bookmakers:
                            if inner_bookmaker["key"] == curr_bookmaker_key:
                                continue

                            for inner_market in inner_bookmaker["markets"]:
                                if inner_market["key"] != "h2h_lay":
                                    continue

                                for inner_outcome in inner_market["outcomes"]:
                                    if inner_outcome["name"] != curr_outcome:
                                        continue  

                                    x = 100  
                                    lay_odds = inner_outcome["price"]

                                    if lay_odds > 0:
                                        inverted_lay_odds = -lay_odds
                                    else:
                                        inverted_lay_odds = abs(lay_odds)

                                    if inverted_lay_odds < 0 and curr_odds < 0:
                                        continue  

                                    if curr_odds > 0:
                                        udog_odds = curr_odds
                                        favs_odds = inverted_lay_odds
                                        udog_book = bookmaker["title"]
                                        favs_book = inner_bookmaker["title"]
                                        udogteam = curr_outcome
                                        favsteam = curr_outcome 
                                    else:
                                        udog_odds = inverted_lay_odds
                                        favs_odds = curr_odds
                                        udog_book = inner_bookmaker["title"]
                                        favs_book = bookmaker["title"]
                                        udogteam = curr_outcome
                                        favsteam = curr_outcome 

                                    y = ((udog_odds / 100) * x) / ((100 / (-favs_odds)) + 1)
                                    winnings = x * (udog_odds / 100) - y
                                    hedge_val = winnings / x
                                    hedge_val = round(hedge_val, 2)

                                    existing_line = db.execute(
                                        """
                                        SELECT 1 FROM all_lines
                                        WHERE udogs_book = ? AND favs_book = ? AND udogs = ? AND favs = ? AND bettype = ?
                                        """,
                                        (udog_book, favs_book, udogteam, favsteam, "lay")
                                    ).fetchone()

                                    if existing_line:
                                        continue

                                    db.execute(
                                        """
                                        INSERT INTO all_lines (
                                            hedge_val,
                                            udogs,
                                            favs,
                                            sport,
                                            bettype,
                                            udogs_odds,
                                            favs_odds,
                                            favs_bet_size,
                                            udogs_book,
                                            favs_book,
                                            hometeam,
                                            awayteam,
                                            point,
                                            commence_time
                                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """,
                                        (
                                            hedge_val,
                                            udogteam,
                                            favsteam,
                                            curr_sport,
                                            "lay", 
                                            udog_odds,
                                            favs_odds,
                                            y,
                                            udog_book,
                                            favs_book,
                                            hometeam,
                                            awayteam,
                                            0,
                                            formatted_time
                                        )
                                    )

    db.commit()
    arbpopulator()
    return flask.render_template('menu.html')
