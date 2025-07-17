from flask import Flask, render_template, request
import requests
import os

from trajanbet import app
import flask
import requests
import sqlite3
from trajanbet.models import get_db
from flask import request 
import ast
from datetime import datetime
from config import ODDS_API_KEY

def convert_odds_to_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

def fetch_event_odds(sport, event_id):
    api_key = ODDS_API_KEY
    url = f"https://api.the-odds-api.com/v4/sports/{sport}/events/{event_id}/odds?apiKey={api_key}&regions=us&markets=h2h,spreads,totals&dateFormat=iso&oddsFormat=american"

    response = requests.get(url)
    odds_data = response.json()
    with open("bayern.txt", "w") as file:
        file.write(str(odds_data))
    return response.json() if response.status_code == 200 else None

def calculate_ev(odds_data):
    highest_ev_details = {}
    ev_results = {"h2h": [], "spreads": [], "totals": []}
    
    for market in ["h2h", "spreads", "totals"]:
        outcome_probs = {}
        for bookmaker in odds_data.get("bookmakers", []):
            for outcome in bookmaker.get("markets", []):
                if outcome["key"] == market:
                    for bet in outcome.get("outcomes", []):
                        team = bet["name"]
                        odds = int(bet["price"])
                        prob = convert_odds_to_probability(odds)
                        
                        if team not in outcome_probs:
                            outcome_probs[team] = []
                        outcome_probs[team].append(prob)

        for team, probs in outcome_probs.items():
            avg_prob = sum(probs) / len(probs)
            for bookmaker in odds_data.get("bookmakers", []):
                for outcome in bookmaker.get("markets", []):
                    if outcome["key"] == market:
                        for bet in outcome.get("outcomes", []):
                            if bet["name"] == team:
                                payout = bet["price"]
                                possible_win = payout if payout > 0 else (100 / -payout) * 100
                                ev = avg_prob * possible_win + ((1 - avg_prob) * -100)

                                ev_results[market].append({
                                    "bookmaker": bookmaker["title"],
                                    "team": team,
                                    "odds": payout,
                                    "ev": round(ev, 2)
                                })
                                if market not in highest_ev_details or ev > highest_ev_details.get(market, {}).get("ev", -100):
                                    highest_ev_details[market] = {
                                        "bookmaker": bookmaker["title"],
                                        "team": team,
                                        "odds": payout,
                                        "ev": round(ev, 2)
                                    }
    return ev_results, highest_ev_details

@app.route("/eventev/<sport>/<event_id>")
def eventev(sport, event_id):
    print("Received sport:", sport)
    print("Received event ID:", event_id)

    odds_data = fetch_event_odds(sport, event_id)
    if not odds_data:
        return "Error fetching odds data", 500
    
    ev_results, highest_ev_details = calculate_ev(odds_data)
    
    return render_template("eventev.html", 
                           sport=odds_data.get("sport_title", "Unknown Sport"),
                           game=f"{odds_data.get('home_team', 'Unknown')} vs {odds_data.get('away_team', 'Unknown')}",
                           ev_results=ev_results,
                           highest_ev_details=highest_ev_details)
