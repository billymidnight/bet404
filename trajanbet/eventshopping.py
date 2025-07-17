import flask
import requests
import random
from datetime import datetime
from trajanbet import app
from trajanbet.models import get_db
from flask import request, render_template
from config import ODDS_API_KEY

@app.route("/eventshopping", methods=["GET"])
def eventshopping():
    """
    Fetches all games and odds for a given sport and stores them in the database.
    Also fetches 10 random sports to display as "Other Popular Sports".
    """
    sport_key = request.args.get("sport_key")
    if not sport_key:
        return "Sport key is required", 400

    api_key = ODDS_API_KEY
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds/?apiKey={api_key}&regions=us&markets=h2h&oddsFormat=american"

    response = requests.get(url)
    if response.status_code != 200:
        return f"API Error: {response.status_code}", 500

    odds_data = response.json()
    txt_file_str = f"{sport_key}_odds.txt"

    with open(txt_file_str, "w") as file:
        file.write(str(odds_data))
    
    db = get_db()

    db.execute("DELETE FROM games WHERE sport_key = ?", (sport_key,))
    db.execute("DELETE FROM odds WHERE game_id IN (SELECT game_id FROM games WHERE sport_key = ?)", (sport_key,))

    unique_bookmakers = set()

    for game in odds_data:
        game_id = game["id"]
        home_team = game["home_team"]
        away_team = game["away_team"]
        commence_time = datetime.strptime(game["commence_time"], "%Y-%m-%dT%H:%M:%SZ")

        db.execute(
            """
            INSERT INTO games (game_id, sport_key, home_team, away_team, commence_time)
            VALUES (?, ?, ?, ?, ?)
            """,
            (game_id, sport_key, home_team, away_team, commence_time)
        )

        for bookmaker in game["bookmakers"]:
            bookmaker_key = bookmaker["key"]
            bookmaker_title = bookmaker["title"]
            unique_bookmakers.add(bookmaker_title)

            db.execute(
                """
                INSERT OR IGNORE INTO bookmakers (key, title)
                VALUES (?, ?)
                """,
                (bookmaker_key, bookmaker_title)
            )

            bookmaker_id = db.execute(
                "SELECT bookmaker_id FROM bookmakers WHERE key = ?", (bookmaker_key,)
            ).fetchone()
            
            if bookmaker_id:
                bookmaker_id = bookmaker_id["bookmaker_id"]

            for market in bookmaker["markets"]:
                if market["key"] != "h2h":
                    continue

                for outcome in market["outcomes"]:
                    outcome_name = outcome["name"]
                    price = outcome["price"]

                    db.execute(
                        """
                        INSERT INTO odds (game_id, bookmaker_id, market, outcome, price)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (game_id, bookmaker_id, "h2h", outcome_name, price)
                    )

    db.commit()

    sport_title = db.execute(
        "SELECT title FROM sports WHERE key = ?", (sport_key,)
    ).fetchone()

    sport_title = sport_title["title"] if sport_title else sport_key.upper()

    games = db.execute(
        "SELECT * FROM games WHERE sport_key = ? ORDER BY commence_time", (sport_key,)
    ).fetchall()

    bookmakers = [row["title"] for row in db.execute("SELECT title FROM bookmakers").fetchall()]

    formatted_games = []
    for game in games:
        game_id = game["game_id"]
        home_team = game["home_team"]
        away_team = game["away_team"]
        commence_time = game["commence_time"]

        odds_data = db.execute(
            """
            SELECT b.title, o.outcome, o.price
            FROM odds o
            JOIN bookmakers b ON o.bookmaker_id = b.bookmaker_id
            WHERE o.game_id = ?
            """,
            (game_id,)
        ).fetchall()

        possible_outcomes = {home_team: "Home", away_team: "Away"}
        for odds in odds_data:
            if odds["outcome"] not in possible_outcomes:
                possible_outcomes[odds["outcome"]] = "Draw"  # Add Draw if it exists

        game_odds = {bookmaker: {outcome: "-" for outcome in possible_outcomes.values()} for bookmaker in bookmakers}
        
        for odds in odds_data:
            bookmaker_name = odds['title']
            outcome = possible_outcomes[odds['outcome']]
            price = odds['price']
            game_odds[bookmaker_name][outcome] = price

        formatted_games.append(
            {
                "game_id": game_id,
                "home_team": home_team,
                "away_team": away_team,
                "commence_time": commence_time,
                "odds": game_odds,
                "possible_outcomes": list(possible_outcomes.values())
            }
        )

    random_sports = db.execute(
        "SELECT key, title FROM sports WHERE key != ? ORDER BY RANDOM() LIMIT 10",
        (sport_key,)
    ).fetchall()

    return render_template(
        "eventshopping.html",
        sport_key=sport_key,
        games=formatted_games,
        bookmakers=bookmakers,
        sport_title=sport_title,
        random_sports=random_sports
    )
