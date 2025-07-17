# __init__.py
import flask

# Create the Flask app
app = flask.Flask(__name__)

# Load configuration settings from config.py
app.config.from_object('config')

# Import the views and models after app creation
import trajanbet.views  # noqa: E402
import trajanbet.aboutpage
import trajanbet.evbetting
import trajanbet.freebet
import trajanbet.pastbets
import trajanbet.riskfree
import trajanbet.linefinder
import trajanbet.arbfinder
import trajanbet.arbitrage
import trajanbet.laypopulate
import trajanbet.lineshopping
import trajanbet.eventshopping

import trajanbet.evbetting
import trajanbet.populateev
import trajanbet.vigcalc
 # noqa: E402

import trajanbet.parimutuel.parimutuel
import trajanbet.parimutuel.settlements
import trajanbet.parimutuel.real
import trajanbet.parimutuel.deleterace

import trajanbet.gpt.gpt

import trajanbet.promo_eval.promo_landing
import trajanbet.promo_eval.sports_eval