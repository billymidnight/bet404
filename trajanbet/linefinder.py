import flask
import requests
from trajanbet import app
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime
from trajanbet.arbitrage import arbpopulator
from config import ODDS_API_KEY


@app.route("/linefinder", methods=["GET", "POST"])
def linefinder():
    db = get_db()
    
    sportsbook = flask.request.form.get("sportsbook", None)
    sport = flask.request.form.get("sport", None)
    live_filter = flask.request.form.get("live", None)
    
    query = "SELECT *, DATETIME(commence_time) as game_time FROM all_lines WHERE favs_book != 'Bovada'"
    params = []
    
    if sportsbook and sportsbook != "allbooks":
        query += " AND udogs_book = ?"
        params.append(sportsbook)
    
    if sport and sport != "allsports":
        query += " AND sport = ?"
        params.append(sport)
    
    query += " ORDER BY hedge_val DESC"
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
    
    return flask.render_template("linefinder.html", lines=filtered_lines)



@app.route("/linepopulator", methods=["GET"])
def linepopulator():
    """
    Populates the all_lines table in the database with hedge_line data.
    """

    sports = ["baseball_mlb", "basketball_nba", "americanfootball_ncaaf", "basketball_ncaab", "icehockey_nhl", ]
    # sports = ["soccer_epl", "soccer_uefa_champs_league", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_italy_serie_b",
    #            "soccer_germany_bundesliga", "soccer_france_ligue_one"]

    db = get_db()

    db.execute("DELETE FROM all_lines")

    all_odds_data = {} 

    for sport in sports:
        api_key = ODDS_API_KEY
        url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}&regions=us,us2&markets=h2h,spreads,totals&oddsFormat=american"

        if sport.startswith("soccer"):
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={api_key}&regions=us&markets=spreads&oddsFormat=american"

        response = requests.get(url)
        print(f"Fetching data for {sport}")

        if response.status_code == 200:
            odds_data = response.json()
            all_odds_data[sport] = odds_data  # Store under sport key
        else:
            print(f"Error: {response.status_code}, {response.text}")

    with open("allodds.txt", "w") as file:
        file.write(str(all_odds_data))


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
            # if curr_sport == "icehockey_nhl":
            #     continue
            
            all_bookmakers = game['bookmakers']

            for bookmaker in all_bookmakers:
                curr_bookmaker_key = bookmaker["key"]

                for market in bookmaker["markets"]:
                    outer_market = market["key"]
                    if outer_market == "h2h_lay":
                        continue
                    outer_point = 0
                    

                    for outcome in market["outcomes"]:
                        curr_outcome = outcome["name"]
                        curr_odds = outcome["price"]

                        if outer_market in ["spreads", "totals"]:
                            outer_point = outcome["point"]

                        for inner_bookmaker in all_bookmakers:
                            if inner_bookmaker["key"] == curr_bookmaker_key:
                                continue

                            for inner_market in inner_bookmaker["markets"]:
                                if inner_market["key"] != outer_market or inner_market == "h2h_lay":
                                    continue
                                curr_mrkt = inner_market["key"]

                                inner_point = 0
                                

                                for inner_outcome in inner_market["outcomes"]:
                                    if inner_outcome["name"] == curr_outcome:
                                        continue
                                    if curr_mrkt in ["totals", "spreads"]:
                                        inner_point = inner_outcome["point"]
                                        if inner_point + outer_point != 0:
                                            continue
                                    
                                    x = 100
                                    hedge_odds = inner_outcome["price"]
                                    
                                    
                                    if hedge_odds < 0 and curr_odds < 0:
                                        continue
                                    elif hedge_odds > 0 and curr_odds > 0:
                                        udog_odds = curr_odds
                                        favs_odds = hedge_odds
                                        udog_book = bookmaker["title"]
                                        favs_book = inner_bookmaker["title"]
                                        udogteam = curr_outcome
                                        favsteam = inner_outcome["name"]

                                        y = ((udog_odds / 100) * x) / ((favs_odds / 100) + 1)
                                        winnings = x * (udog_odds / 100) - y
                                        hedge_val = winnings / x
                                    else:
                                        if curr_odds > 0:
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

                                        y = ((udog_odds / 100) * x) / ((100 / (-favs_odds)) + 1)
                                        winnings = x * (udog_odds / 100) - y
                                        hedge_val = winnings / x

                                    hedge_val = round(hedge_val, 2)
                                    # Prevent duplicate lines
                                    existing_line = db.execute(
                                        """
                                        SELECT 1 FROM all_lines
                                        WHERE udogs_book = ? AND favs_book = ? AND udogs = ? AND favs = ?
                                        """,
                                        (udog_book, favs_book, udogteam, favsteam)
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

    
    arbpopulator()
    db.commit()
    return flask.render_template('menu.html')


