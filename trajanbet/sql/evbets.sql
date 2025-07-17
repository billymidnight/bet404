CREATE TABLE evbets (
    evbetid INTEGER PRIMARY KEY AUTOINCREMENT,
    ev REAL NOT NULL,
    sport TEXT NOT NULL,
    outcome TEXT NOT NULL,
    outcome_odds INTEGER NOT NULL,
    book TEXT NOT NULL,
    implied_prob REAL NOT NULL,
    avg_implied_prob REAL NOT NULL,
    commence_time DATETIME NOT NULL,
    hometeam TEXT NOT NULL,
    awayteam TEXT NOT NULL
);
