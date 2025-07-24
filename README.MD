# 🏛️ Trajan Betting Central (TBC)

**Trajan Betting Central** is a Flask-based sports trading and analytics platform that empowers users with the sharpest tools in the betting space — from EV calculators to line finders, vig analysis, and arbitrage detection.

## ⚙️ Technologies Used

- **Python 3**, **Flask** for backend
- **SQLite3** for lightweight DB storage
- **HTML/CSS/JS** for front-end UI
- **Jinja2** for templating
- **OddsAPI / allodds.txt** data source (raw bookmaker odds dump)

---

## 📁 Directory Structure (Key Files)


---

## 🧠 Core Features

### 🧮 Expected Value (EV) Calculator
- Route: `/ev_populate/`
- Reads `allodds.txt` → parses H2H market odds
- For each bookmaker, calculates **vig-free probabilities** by:
  - Converting American odds to implied probabilities
  - Summing to find total book (vig)
  - Normalizing each outcome by dividing by the total book
- Averages probabilities across books to get “true odds”
- Calculates expected value (EV) for each outcome per book:
  
  \[
  EV = (true\_prob \times payout) + ((1 - true\_prob) \times -100)
  \]

- Stores result in `evbets` table with fields:
  - `ev`, `outcome`, `odds`, `book`, `avg_prob`, `implied_prob`, etc.

---

### 📈 Vig Calculator Tool
- Button on main menu → `/vig_calc/`
- Two input fields:
  - Outcome 1 American odds
  - Outcome 2 American odds
- Backend logic:
  - Converts odds to implied probabilities (handles both +/- odds)
  - Sums them to find **vig (overround)**
  - Normalizes probabilities to create **vig-free true odds**
  - Converts these back to American odds
- Displays:
  - Vig as percentage (e.g. 6.3%)
  - True implied probabilities
  - Vig-free odds

---

### 📊 EV Table UI (optional if rendering in progress)
- A frontend table view of all calculated EV bets.
- Possible filters: sport, book, EV threshold, teams.

---

## 🔧 Helper Functions (helpers.py or within app)

```python
def convert_odds_to_probability(odds):
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)

def probability_to_american(prob):
    if prob == 0:
        return float('inf')
    elif prob >= 0.5:
        return int(-100 * prob / (1 - prob))
    else:
        return int((1 - prob) / prob * 100)

Arbitrage Populator (/arbpopulator)
The arbpopulator route populates the arb_lines table with arbitrage betting opportunities by parsing through the full JSON odds dump (allodds.txt) for all supported sports and searching for pricing inefficiencies across bookmakers.

Purpose
Identify risk-free profit scenarios (arbitrage bets) between different sportsbooks by comparing prices for opposing outcomes (e.g., one book has Team A at +200, another has Team B at -150).

Core Logic
Parse the odds from the local dump file.

Loop through all games and extract:

Game metadata (teams, commence time)

Odds for each outcome from all available sportsbooks.

Compare each price with every other sportsbook for:

Matching outcomes (same team or point spread)

Opposite outcomes (for arbitrage).

Calculate the arbitrage margin:
Let:
  A = underdog odds (positive)
  B = favorite odds (positive)

Then:
  Stake B: x
  Stake A: y = (A + 100) / ((B / 100) + 1)
  Payout from A win = A
  Net profit = A - y
  Margin = (A - y) / 100
Let:
  A = positive odds
  B = negative odds

Then:
  y = (A + 100) / ((100 / -B) + 1)
  Margin = (A - y) / 100

graph TD
    A[Start: /arbpopulator] --> B[Read allodds.txt]
    B --> C{For each Game}
    C --> D[Extract teams, time, sport]
    D --> E[Loop Bookmakers]
    E --> F[Loop Markets (h2h, spreads, totals)]
    F --> G[Find outcome odds]
    G --> H[Compare against other bookmakers]
    H --> I[Check valid arbitrage combo]
    I --> J[Calculate margin]
    J --> K{Margin > 0?}
    K -->|Yes| L[Insert into arb_lines]
    K -->|No| M[Skip]
    L --> N[Done]
    M --> N


Event Shopping (/eventshopping)
This endpoint fetches live odds data from the Odds API for a given sport and populates three core database tables:

games – game metadata

odds – odds per outcome per bookmaker

bookmakers – unique bookmakers participating

Also prepares the line shopping UI page, where users can compare odds across books for each outcome of a match.

Core Logic
User specifies a sport_key via URL (e.g., basketball_nba).

Trajan fetches live JSON odds from the Odds API for that sport.

Writes response to {sport_key}_odds.txt.

Loops through all games and:

Inserts metadata into games

For each bookmaker, inserts bookmaker data if not already present

For each market, inserts odds data per outcome

Renders a sortable table of all games + odds from all books.

Line Shopping Display
The front-end (eventshopping.html) presents a comparison matrix:

Rows: games

Columns: bookmakers

Cells: odds for Home, Away, and Draw

It allows quick comparison to find best prices across markets.

Tables Affected
games
bookmakers
odds


Let’s say:

Bet365 has Team A at +200

FanDuel has Team B at -150

Then:
Stake on +200 = $100 (returns $200 profit if win)
To hedge -150:

y = (200 + 100) / ((100 / 150) + 1) = 300 / (0.666 + 1) = 300 / 1.666 = ~$180

Risk: $100 + $180 = $280
Win either way: $300

Profit: $20, margin = 20 / 280 ≈ 7.14%
Stored in arb_lines.

Absolutely, let’s keep cooking this README like gods of old Rome. Here's the next section for the README.md covering both:

Promo Evaluator (Casino + Sports)

Vig Calculator (Devig Tool)

All styled in the same glorious classical tone as your earlier sections, with clean breakdowns and a mermaid flow diagram to capture the logic visually.

Promo Evaluator
The Promo Evaluator tool allows users to analyze casino and sports rebate promotions using Monte Carlo simulations. Users input parameters like rebate size, playthrough, odds, and house edge, and Trajan runs thousands of simulations to output profitability, EV, bust rates, and more.

Features
Casino Rebate Simulation: Estimates final bankroll using base and fallback strategies depending on bust.

Sports Rebate Simulation: Simulates x days of betting with rebate recovery mechanics.

Allows toggling between Casino and Sports modes using in-page buttons.

Returns core metrics: EV in $, EV %, standard deviation, bust %, and raw bankroll trajectory from last 10 simulations.

Casino Mechanics
Each simulation starts with rebate_amount and bets initial_bet_size until either the target is hit or balance drops to zero.

Upon bust, fallback to a rebate recovery strategy that bets in smaller chunks until the playthrough is satisfied or funds run out.

Dynamic handling for true playthrough calculated as:

ini
Copy
Edit
true_playthrough = playthrough / (contribution % / 100)
Sports Mechanics
Simulates daily betting with primary and rebate odds (odds_initial, odds_rebate) adjusted for vig.

For every day:

If initial bet wins → payout.

If initial bet loses → attempt rebate bet.

Repeats this cycle over days and iterations to assess risk of busting and expected final value.

Sample Output

Mean Ending Balance: $167.83
Expected Net Profit: $42.83
Standard Deviation: 21.51
Bust Percentage: 26.0%
Expected Value: +25.6%

Backend Logic
Routes:

GET /promoevaluator → Render form

POST /promoevaluator → Run casino promo sim

POST /sports_evaluator → Run sports rebate sim

Simulation engine uses random.choices() with controlled edge to simulate betting outcome per round.

Vig Calculator (De-Vig Tool)
This tool calculates the vig (overround) of a 2-outcome market, and then gives the vig-free true odds.

Inputs
Outcome 1 Odds (American)

Outcome 2 Odds (American)

Computation

1. Convert American odds to implied probability:
+Odds: 100 / (odds + 100)
-Odds: -odds / (-odds + 100)


2. Compute Book %:
book = p1 + p2
vig = book - 1

3. Normalize to remove vig:
vigfree_p1 = p1 / book
vigfree_p2 = p2 / book

4. Convert back to American:
if decimal >= 2.0: (decimal - 1) * 100
else: -100 / (decimal - 1)

NOTE: Vig method used currently is Pro-rata (normalization). Other methods underway (including but not limited to power, subtraction, Shin's)

graph TD
  A[User submits form] --> B{Form Type?}
  B -- Casino --> C[Run Casino Monte Carlo]
  B -- Sports --> D[Run Sports Monte Carlo]
  C --> E[Check bust or success]
  D --> E
  E --> F[Calculate metrics: EV, stddev, bust%]
  F --> G[Render promoevaluator.html]

  B2[User enters 2 American Odds] --> H[Convert to Implied Probabilities]
  H --> I[Calculate Book % and Vig]
  I --> J[Normalize probs to remove vig]
  J --> K[Convert to Vig-Free Odds]
  K --> L[Render vig_calc.html with results]

Absolutely — here's a beautifully overwaffled, scientifically-toned README section for your Hadrian chatbot, integrating RAG, custom logic routing, and multimodal function access across the full stack of Trajan Betting Central tools.

🧠 Hadrian – The AI Betting Strategist of Trajan Betting Central
Hadrian is the GPT-powered Roman mind behind Trajan Betting Central — a domain-aware assistant trained to parse, guide, and advise users through the powerful analytical tools on the platform. But this is no ordinary chatbot. Hadrian uses an advanced Retrieval-Augmented Generation (RAG) pipeline layered with custom prompt engineering, route parsing, and dynamic backend access to perform intelligent reasoning on user queries — in real-time.

Hadrian is designed not to “answer questions” — but to operate your tools. Whether a user wants to evaluate a +230 / -290 line's vig, explore optimal rebate strategy, or scan the line finder table for arbitrage edges, Hadrian serves as the front-facing LLM interface to execute the command pipeline.

🔍 Features
RAG-Powered Retrieval Layer:
Uses a custom-built retrieval pipeline across SQLite3 tables and HTML interface docstrings (Line Finder, Arbitrage Finder, Promo Evaluator, and Odds Screen).

Structured Prompt Engineering:
Queries are translated into structured JSON command forms that internally route to calculation modules or SQL selectors, including:

vig_calc() for true odds calculations

promoevaluator() for Monte Carlo rebate simulations

linefinder_search(), arb_finder(), etc. for data scraping

Fallbacks to Python Evaluation and String Matching:
If no relevant RAG content is retrieved or tables are ambiguous, Hadrian smartly routes the query to specific tools via fuzzy prompt-keyword dispatch.

Multi-Table Awareness:
Hadrian maintains awareness of schema definitions for tables like:

-> line_finder_table
-> arbitrage_finder_table
-> promo_eval_table
-> odds_screen_table
-> any new analytical calculators registered under Flask.

RAG-to-Action Flow
mermaid
Copy
Edit
graph TD
    A[User Query] --> B[Prompt Router]
    B --> C{Does prompt match a tool?}
    C -->|Yes| D[Flask Route Dispatcher]
    D --> E1[Promo Evaluator]
    D --> E2[Vig Calculator]
    C -->|No| F[Query Embedder → Vector Store]
    F --> G[SQLite Table Retriever]
    G --> H[Custom Prompt Generator (w/ data)]
    H --> I[LLM (GPT-4)]
    I --> J[Final Structured Response]

    style A fill:#e1eaff,stroke:#0078D4,stroke-width:2px
    style J fill:#fef6c3,stroke:#dcb300,stroke-width:2px
Example Prompts
“What’s the true probability if the odds are +145 and -165?”

→ Converts to vig_calc(+145, -165)

→ Returns the overround and true odds

“Evaluate a $50 casino rebate with 10x playthrough and 10% contribution.”

→ Converts to promoevaluator() with prefilled fields

→ Runs Monte Carlo, returns bust %, EV, stddev, and last 10 outcomes

“Any arbitrages between FanDuel and Bet365 today?”

→ Routes to arb_finder() and scrapes arbitrage table

“What’s the EV if I take -110 every day for 5 days with a rebate on losses?”

→ Auto-structured to use sports_evaluator() with a custom simulation

Tech Stack and Dependencies
LLM: OpenAI GPT-4o with function-calling enabled

RAG: Local SQLite vector store (Qdrant optional for scalability)

Prompt Router: Regex and keyword-based dispatcher with schema-sensitive logic

Frontend: Rendered via /gptasker HTML template with styled chat bubble UI

API Integration: Internal Flask API endpoints for:

vig_calc, promoevaluator, sports_evaluator, etc.

Security & Guardrails
All external tool usage routed through safe parameter bindings.

LLM execution constrained to pre-approved Flask endpoints.

No direct SQL execution from untrusted user prompts.

Future Upgrades
Implement voice activation (e.g., “Hadrian, evaluate the vig”)

Natural language chart requests (e.g., “Show me bust % distribution” → graph)

Memory persistence and daily edge reports from scraped books

GPT-generated matched betting walkthroughs based on current promotions