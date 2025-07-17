import flask
import requests
from trajanbet import app
from trajanbet.models import get_db
from flask import request, render_template
from flask import redirect, url_for
from config import ODDS_API_KEY

@app.route("/realmarkets", methods=["GET"])
def realmarkets():
    """
    Fetches and displays all available sports with betting markets.
    """
    api_key = ODDS_API_KEY
    db = get_db()

    response = requests.get(f"https://api.the-odds-api.com/v4/sports/?apiKey={api_key}")
    
    if response.status_code == 200:
        sports_data = response.json()

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
    
    sports = db.execute("SELECT key, title, description, active FROM sports ORDER BY title ASC").fetchall()

    return render_template("realmarkets.html", sports=sports)

@app.route("/realgame/<sport_key>")
def realgame(sport_key):
    """
    Fetch all upcoming games for a specific league/sport using the Events API (not Odds API).
    """
    api_key = ODDS_API_KEY
    url = f"https://api.the-odds-api.com/v4/sports/{sport_key}/events?apiKey={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return "API Error", 500

    games_data = response.json()

    db = get_db()
    random_sports = db.execute(
        "SELECT key, title FROM sports WHERE key != ? ORDER BY RANDOM() LIMIT 10", (sport_key,)
    ).fetchall()

    formatted_games = []
    for game in games_data:
        sport_title = game["sport_title"]
        formatted_games.append({
            "home_team": game["home_team"],
            "away_team": game["away_team"],
            "commence_time": game["commence_time"],
            "event_id": game["id"]
        })

    return render_template("realgame.html", sport_title=sport_title, sport_key=sport_key, games=formatted_games, random_sports=random_sports)

@app.route("/createmarket/<sport>/<event_id>", methods=["GET"])
def createmarket(sport, event_id):
    """
    Display form for creating a parimutuel market, forcing the user to pick Moneyline.
    """
    api_key = ODDS_API_KEY
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events?apiKey={api_key}"

    response = requests.get(url)
    if response.status_code != 200:
        return "API Error", 500

    events_data = response.json()
    
    home_team, away_team = None, None
    for game in events_data:
        if game["id"] == event_id:
            home_team = game["home_team"]
            away_team = game["away_team"]
            break

    if not home_team or not away_team:
        return "Error: Could not find game details.", 500

    markets = [{"key": "h2h", "name": "Moneyline"}]

    return render_template("createmarket.html", 
                           sport=sport, 
                           event_id=event_id, 
                           home_team=home_team, 
                           away_team=away_team, 
                           markets=markets)

@app.route("/create_real_race/<sport>/<event_id>", methods=["POST"])
def create_real_race(sport, event_id):
    """
    Creates a real parimutuel race for the selected market (Moneyline) and inserts it into the database.
    """
    selected_market = request.form.get("selected_market")
    if not selected_market:
        return "Market selection is required.", 400

    api_key = ODDS_API_KEY
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds?apiKey={api_key}&regions=us,uk&dateFormat=iso&oddsFormat=american"

    response = requests.get(url)
    if response.status_code != 200:
        return "API Error", 500

    odds_data = response.json()
    if not odds_data or "bookmakers" not in odds_data or not odds_data["bookmakers"]:
        return "No odds available for this event.", 500

    home_team = odds_data.get("home_team", "Unknown")
    away_team = odds_data.get("away_team", "Unknown")
    commence_time = odds_data.get("commence_time", "Unknown")

    game_name = f"{home_team} vs {away_team}"
    race_name = f"{game_name} - {selected_market.title().replace('_', ' ')}"
    race_venue = odds_data.get("sport_title", sport)

    selected_market_data = None
    for bookmaker in odds_data["bookmakers"]:
        for market in bookmaker["markets"]:
            if market["key"] == "h2h":  
                selected_market_data = market
                break
        if selected_market_data:
            break

    if not selected_market_data:
        return "Market data unavailable.", 500

    horses = [{"name": outcome["name"], "odds": outcome["price"]} for outcome in selected_market_data["outcomes"]]

    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """
        INSERT INTO races (racename, racevenue, type, sport_key, event_id, commence_time)
        VALUES (?, ?, 'real', ?, ?, ?)
        """,
        (race_name, race_venue, sport, event_id, commence_time),
    )
    race_id = cursor.lastrowid

    for horse in horses:
        cursor.execute(
            """
            INSERT INTO horses (raceid, horsename, opening_odds)
            VALUES (?, ?, ?)
            """,
            (race_id, horse["name"], horse["odds"]),
        )

    db.commit()
    return redirect(url_for("onerace", race_id=race_id))
