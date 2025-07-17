import flask
from trajanbet import app
from trajanbet.models import get_db 

@app.route('/riskfree/', methods=["GET"])
def risk_free_bet_calculator():
    return 0