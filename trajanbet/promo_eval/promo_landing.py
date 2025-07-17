from flask import Flask, render_template, request, redirect, url_for
from trajanbet import app
from trajanbet.models import get_db
import datetime
from datetime import datetime
from math import gcd
import random
import statistics

def rebate_runner(rebate_value, true_playthru, betsize = 25, house_edge = 0.5, early_betsize = 250):
    print(f"Early bet size is {early_betsize}")
    basebetsize = betsize
    wager_requirement = rebate_value * true_playthru
    print(f"This is the wager requirement: {wager_requirement}")
    w1 = (1 + house_edge/100) / 2
    w2 = 1 - w1
    weights = [w1, w2]
    results = ['lose', 'win']

    if true_playthru <= 5:
        bankroll = rebate_value
        amount_wagered = 0
        while True:
            betsize = min(betsize, bankroll)
            outcome = random.choices(results, weights=weights, k = 1)[0]

            if outcome == 'lose':
                bankroll -= betsize
            else:
                bankroll += betsize
            amount_wagered += betsize
            if amount_wagered >= wager_requirement:
                return bankroll
            if bankroll <= 0:
                return 0
    else:
        bankroll = rebate_value
        amount_wagered = 0
        betsize = early_betsize
        while True:
            betsize = min(betsize, bankroll)
            outcome = random.choices(results, weights=weights, k = 1)[0]

            if outcome == 'lose':
                bankroll -= betsize
            else:
                bankroll += betsize
            amount_wagered += betsize
            if amount_wagered >= wager_requirement:
                return bankroll
            if bankroll <= 0:
                return 0
            if bankroll >= (true_playthru * rebate_value) / 6:
                betsize = basebetsize








@app.route("/promoevaluator", methods=["GET"])
def promolanding():
    return render_template("promoevaluator.html", nosubmission=True)

@app.route("/promoevaluator", methods=["POST"])
def promoevaluator():
    rebate_amount = float(request.form['rebate_amount'])

    playthrough = float(request.form['playthrough'])

    contribution = float(request.form['contribution'])

    target = float(request.form['target'])

    iterations = int(request.form['iterations'])

    house_edge_input = request.form.get('house_edge')
    house_edge = float(house_edge_input) if house_edge_input else 0.5

    initial_bet_size = request.form['initial_bet_size']
    initial_bet_size = float(initial_bet_size) if initial_bet_size else rebate_amount / 5

    early_bet_size = request.form['early_betsize']
    early_bet_size = float(early_bet_size) if early_bet_size else rebate_amount / 5

    true_playthru = playthrough / (contribution * 0.01)
    print(f"True Playthrough Requirement: {true_playthru}")

    print(f"True playthrough is {playthrough}")
    hits = 0
    misses = 0
    scores = []
    for _ in range(iterations):
        bankroll = rebate_amount
        basebetsize = initial_bet_size
        w1 = (1 + house_edge/100) / 2
        w2 = 1 - w1
        weights = [w1, w2]
        results = ['lose', 'win']

        

        while True:
            betsize = min(basebetsize, bankroll)
            outcome = random.choices(results, weights=weights, k = 1)[0]
            # print(outcome)
            if outcome == 'lose':
                bankroll -= betsize
                
            else:
                bankroll += betsize                
            
            if bankroll >= target:
                hits += 1
                scores.append(bankroll)
                break
            if bankroll <= 0:
                
                misses += 1
                
                rebate_return = rebate_runner(rebate_value=rebate_amount, true_playthru=true_playthru, house_edge=house_edge, betsize=rebate_amount/50, early_betsize=early_bet_size)
                scores.append(rebate_return) 
                break              

    mean_ending_balance = sum(scores) / len(scores)
    expected_pandl = mean_ending_balance - rebate_amount
    percent_target_reached = (hits / iterations) * 100
    percent_bust = 100 - percent_target_reached
    ev_percentage = (expected_pandl / rebate_amount) * 100

    last_10_results = [round(x - rebate_amount, 2) for x in scores[-10:]]

    pnl_list = [x - rebate_amount for x in scores]
    stddev = statistics.pstdev(pnl_list)

    print(f"True playthrough is {true_playthru}")
    context = {
        "mean_ending_balance": round(mean_ending_balance, 2),
        "expected_pandl": round(expected_pandl, 2),
        "stddev": round(stddev, 2),
        "percent_target_reached": round(percent_target_reached, 2),
        "percent_bust": round(percent_bust, 2),
        "ev_percentage": round(ev_percentage, 2),
        "last_10_results": last_10_results,
        "rebate_amount": rebate_amount,
        "playthrough": playthrough,
        "contribution": contribution,
        "iterations": iterations,
        "target": target,
        "house_edge": house_edge,
        "early_bet_size": early_bet_size,
        "initial_bet_size": initial_bet_size
    } 


    result = {
        "ev": "$123.45",
        "mean": "$132.10",
        "stddev": "$24.50",
        "bust": 32.1,
        "survive": 67.9
    }
    return render_template("promoevaluator.html", nosubmission=False, **context)
