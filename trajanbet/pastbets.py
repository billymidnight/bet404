import flask
from trajanbet import app
from trajanbet.models import get_db 

@app.route('/pastbets/', methods=["GET"])
def past_bets():
    return 0