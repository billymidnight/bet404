CREATE TABLE games (
    game_id TEXT PRIMARY KEY,
    sport_key TEXT NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    commence_time DATETIME NOT NULL
);

CREATE TABLE bookmakers (
    bookmaker_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL
);

CREATE TABLE odds (
    odd_id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    bookmaker_id INTEGER NOT NULL,
    market TEXT NOT NULL,
    outcome TEXT NOT NULL,
    price INTEGER NOT NULL
);
