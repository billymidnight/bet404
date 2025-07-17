create table arb_lines (
    line_id integer primary key autoincrement,
    arb_margin real not null,
    udogs varchar(200) not null,
    favs varchar (200) not null,
    sport varchar (200) not null,
    bettype varchar(200) not null,
    udogs_odds int not null,
    favs_odds int not null,
    favs_bet_size real not null,
    udogs_book varchar(200) not null,
    favs_book varchar(200) not null,
    commence_time datetime not null,
    hometeam varchar(200),
    awayteam varchar(200),
    point real
)