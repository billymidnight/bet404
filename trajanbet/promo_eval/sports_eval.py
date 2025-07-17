from flask import request, render_template
from trajanbet import app
import random
import statistics

@app.route("/sports_evaluator", methods=["POST"])
def sports_evaluator():
    rebate_amount = float(request.form['sports_rebate'])
    odds_initial = int(request.form['odds_initial'])
    odds_rebate = int(request.form['odds_rebate'])
    vig = float(request.form['vig']) / 100  # Convert % to decimal
    days = int(request.form['days'])
    iterations = int(request.form['iterations'])

    # Calculate win probabilities for both bets
    prob_initial = (100 / (odds_initial + 100)) * (1 - vig)
    prob_rebate = (100 / (odds_rebate + 100)) * (1 - vig)

    results = ['lose', 'win']
    weights_initial = [1 - prob_initial, prob_initial]
    weights_rebate = [1 - prob_rebate, prob_rebate]

    scores = []
    busts = 0

    for _ in range(iterations):
        bankroll = days * rebate_amount

        for _day in range(days):
            outcome = random.choices(results, weights=weights_initial, k=1)[0]

            if outcome == "win":
                bankroll += rebate_amount * (odds_initial / 100)
            else:
                bankroll -= rebate_amount
                rebate_outcome = random.choices(results, weights=weights_rebate, k=1)[0]
                if rebate_outcome == "win":
                    bankroll += rebate_amount * (odds_rebate / 100)

            if bankroll <= 0:
                busts += 1
                break

        scores.append(bankroll)

    # Final metrics
    mean_bankroll = sum(scores) / len(scores)
    expected_pnl = mean_bankroll - (days * rebate_amount)
    stddev = statistics.pstdev([x - (days * rebate_amount) for x in scores])
    ev_percentage = (expected_pnl / (days * rebate_amount)) * 100

    vig = round(vig * 100, 2)
    last_10_results = [round(x - (days * rebate_amount), 2) for x in scores[-10:]]
    bust_percentage = (busts / iterations) * 100
    context = {
        "mean_ending_balance": round(mean_bankroll, 2),
        "expected_pandl": round(expected_pnl, 2),
        "stddev": round(stddev, 2),
        "ev_percentage": round(ev_percentage, 2),
        "percent_target_reached": None,
        "last_10_results": last_10_results,
        "sports_rebate": rebate_amount,
        "playthrough": None,
        "contribution": None,
        "iterations": iterations,
        "odds_initial": odds_initial,
        "odds_rebate": odds_rebate,
        "vig": vig,
        "days": days,
        "percent_bust": round(bust_percentage, 2)
        
    }

    return render_template("promoevaluator.html", nosubmission=False, fromsports=True, **context)
