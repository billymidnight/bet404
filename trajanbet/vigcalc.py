from flask import request, render_template
from trajanbet import app

@app.route("/vig_landing", methods=["GET"])
def vig_landing():
    return render_template("vig_calc.html", noSubmission=True)

@app.route("/vig_calc", methods=["POST"])
def vig_calc():
    odds1 = int(request.form["odds1"])
    odds2 = int(request.form["odds2"])

    def implied_prob(odds):
        if odds > 0:
            return 100 / (odds + 100)
        else:
            return -odds / (-odds + 100)

    p1 = implied_prob(odds1)
    p2 = implied_prob(odds2)
    book = p1 + p2
    vig = book - 1

    vigfree_p1 = p1 / book
    vigfree_p2 = p2 / book

    d1 = 1 / vigfree_p1
    d2 = 1 / vigfree_p2

    def decimal_to_american(decimal):
        if decimal >= 2.0:
            return int((decimal - 1) * 100)
        else:
            return int(-100 / (decimal - 1))

    vigfree_odds1 = decimal_to_american(d1)
    vigfree_odds2 = decimal_to_american(d2)

    context = {
        "nosubmission": False,
        "odds1": odds1,
        "odds2": odds2,
        "vig": round(vig * 100, 2),
        "vigfree_odds1": vigfree_odds1,
        "vigfree_odds2": vigfree_odds2
    }

    return render_template("vig_calc.html", **context)
