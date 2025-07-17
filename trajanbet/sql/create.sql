create table bets (
    betid integer primary key autoincrement,
    game varchar(200),
    line varchar(200),
    udogsbook varchar(200),
    udogsodss int not null,
    favsbook varchar(200),
    favsodds int not null,
    udogsamount numeric,
    favsamount numeric,
    winnings numeric not null,
    hedge_value numeric not null
);

create table default_freebet (
    game varchar(200),
    line varchar(200),
    udogodds numeric,
    favsodds numeric,
    betamount numeric
);

insert into default_freebet values 
("Bayern Munich vs. VFL Wolfsburg", "Over/Under 4.5", 260, 300, 100);

create table all_lines (
    line_id integer primary key autoincrement,
    hedge_val real not null,
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

