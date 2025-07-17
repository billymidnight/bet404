CREATE TABLE races (
    raceid INTEGER PRIMARY KEY AUTOINCREMENT,
    racename TEXT NOT NULL,
    racevenue TEXT NOT NULL,
    completed BOOLEAN DEFAULT 0,
    sport_key VARCHAR,
    event_id VARCHAR,
    commence_time TEXT,
    home_score INTEGER,
    away_score INTEGER,
    type VARCHAR NOT NULL
);

CREATE TABLE horses (
    horseid INTEGER PRIMARY KEY AUTOINCREMENT,
    horsename TEXT NOT NULL,
    raceid INTEGER,
    position_finished INTEGER DEFAULT NULL,
    opening_odds INTEGER,
    FOREIGN KEY (raceid) REFERENCES races(raceid)
);

CREATE TABLE racebets (
    betid INTEGER PRIMARY KEY AUTOINCREMENT,
    betamount REAL NOT NULL,
    bettorname TEXT NOT NULL,
    horseid INTEGER,
    active_or_settled TEXT CHECK(active_or_settled IN ('active', 'settled')),
    FOREIGN KEY (horseid) REFERENCES horses(horseid)
);
