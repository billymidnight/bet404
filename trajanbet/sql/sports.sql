create table sports (
    sport_id integer primary key autoincrement,
    key varchar(200) not null,
    title varchar(200) not null,
    description varchar(300) not null,
    active bool not null,
    has_outright bool not null
)