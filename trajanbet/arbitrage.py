import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime

@app.route("/arbpopulator", methods=["GET"])
def arbpopulator():
    """
    Populates the all_lines table in the database with hedge_line data.
    """

    sports = ["americanfootball_nfl", "basketball_nba", "americanfootball_ncaaf", "basketball_ncaab", "icehockey_nhl"]
    # sports = ["soccer_epl", "soccer_uefa_champs_league", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_italy_serie_b",
    #           "soccer_germany_bundesliga", "soccer_france_ligue_one"]

    db = get_db()

    db.execute("DELETE FROM arb_lines")

    with open("allodds.txt", "r") as file:
        data = file.read()

    odds_data = ast.literal_eval(data)  

    for sport, games in odds_data.items():  
        for game in games:
            gametime = game["commence_time"]
            formatted_time = datetime.strptime(gametime, "%Y-%m-%dT%H:%M:%SZ")
            hometeam = game["home_team"]
            awayteam = game["away_team"]
            curr_sport = game["sport_key"]
            if curr_sport == "icehockey_nhl":
                continue
            all_bookmakers = game['bookmakers']

            for bookmaker in all_bookmakers:
                curr_bookmaker_key = bookmaker["key"]
                print("Outer bookmaker:", curr_bookmaker_key)

                for market in bookmaker["markets"]:
                    outer_market = market["key"]
                    outer_point = 0
                    if outer_market in ["spreads", "totals"]:
                        outer_point = market["outcomes"][0]["point"]

                    for outcome in market["outcomes"]:
                        curr_outcome = outcome["name"]
                        curr_odds = outcome["price"]
                        if outer_market == "h2h_lay":
                            curr_odds = -curr_odds
                        print("Outer outcome:", curr_outcome, "Odds:", curr_odds)

                        for inner_bookmaker in all_bookmakers:
                            if inner_bookmaker["key"] == curr_bookmaker_key:
                                continue
                            print("Inner bookmaker key:", inner_bookmaker["key"])

                            for inner_market in inner_bookmaker["markets"]:
                                if inner_market["key"] != outer_market:
                                    continue
                                curr_mrkt = inner_market["key"]

                                inner_point = 0
                                if curr_mrkt in ["totals", "spreads"]:
                                    inner_point = inner_market["outcomes"][0]["point"]
                                    if abs(inner_point) != abs(outer_point):
                                        continue

                                for inner_outcome in inner_market["outcomes"]:
                                    if inner_outcome["name"] == curr_outcome:
                                        continue
                                    x = 100
                                    hedge_odds = inner_outcome["price"]
                                    if inner_market["key"] == "h2h_lay":
                                        hedge_odds = -hedge_odds

                                    if hedge_odds + curr_odds <= 0:
                                        continue
                                    elif hedge_odds > 0 and curr_odds > 0:
                                        udog_odds = curr_odds
                                        favs_odds = hedge_odds
                                        udog_book = bookmaker["title"]
                                        favs_book = inner_bookmaker["title"]
                                        udogteam = curr_outcome
                                        favsteam = inner_outcome["name"]

                                        y = (udog_odds + 100) / ((favs_odds / 100) + 1)
                                        winnings = udog_odds - y
                                        arb_margin = winnings / 100
                                    else:
                                        if curr_odds > hedge_odds:
                                            udog_odds = curr_odds
                                            favs_odds = hedge_odds
                                            udog_book = bookmaker["title"]
                                            favs_book = inner_bookmaker["title"]
                                            udogteam = curr_outcome
                                            favsteam = inner_outcome["name"]
                                        else:
                                            udog_odds = hedge_odds
                                            favs_odds = curr_odds
                                            udog_book = inner_bookmaker["title"]
                                            favs_book = bookmaker["title"]
                                            udogteam = inner_outcome["name"]
                                            favsteam = curr_outcome

                                        y = (udog_odds + 100) / ((100 / -favs_odds) + 1)
                                        winnings = udog_odds - y
                                        arb_margin = winnings / 100

                                    arb_margin = round(arb_margin, 2)

                                    # Prevent duplicate lines
                                    existing_line = db.execute(
                                        """
                                        SELECT 1 FROM arb_lines
                                        WHERE udogs_book = ? AND favs_book = ? AND udogs = ? AND favs = ?
                                        """,
                                        (udog_book, favs_book, udogteam, favsteam)
                                    ).fetchone()

                                    if existing_line:
                                        continue

                                    db.execute(
                                        """
                                        INSERT INTO arb_lines (
                                            arb_margin,
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
                                            arb_margin,
                                            udogteam,
                                            favsteam,
                                            curr_sport,
                                            outer_market,  
                                            udog_odds,
                                            favs_odds,
                                            y,
                                            udog_book,
                                            favs_book,
                                            hometeam,
                                            awayteam,
                                            outer_point,
                                            formatted_time
                                        )
                                    )
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

                    if outer_market != "h2h":  # Skip non-h2h markets for regular bets
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

                                    if inverted_lay_odds + curr_odds < -40:
                                        print("ah failed at the summit\n")
                                        continue  
                                    elif inverted_lay_odds > 0 and curr_odds > 0:
                                        udog_odds = curr_odds
                                        favs_odds = inverted_lay_odds
                                        udog_book = bookmaker["title"]
                                        favs_book = inner_bookmaker["title"]
                                        udogteam = curr_outcome
                                        favsteam = inner_outcome["name"]

                                        y = (udog_odds + 100) / ((favs_odds / 100) + 1)
                                        winnings = udog_odds - y
                                        arb_margin = winnings / 100
                                    else:
                                        if curr_odds > inverted_lay_odds:
                                            udog_odds = curr_odds
                                            favs_odds = inverted_lay_odds
                                            udog_book = bookmaker["title"]
                                            favs_book = inner_bookmaker["title"]
                                            udogteam = curr_outcome
                                            favsteam = inner_outcome["name"]
                                        else:
                                            udog_odds = inverted_lay_odds
                                            favs_odds = curr_odds
                                            udog_book = inner_bookmaker["title"]
                                            favs_book = bookmaker["title"]
                                            udogteam = inner_outcome["name"]
                                            favsteam = curr_outcome 
                                        y = (udog_odds + 100) / ((100 / -favs_odds) + 1)
                                        winnings = udog_odds - y
                                        arb_margin = winnings / 100

                                    arb_margin = round(arb_margin, 2)

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
                                        INSERT INTO arb_lines (
                                            arb_margin,
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
                                            arb_margin,
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