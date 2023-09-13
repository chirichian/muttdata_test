CREATE TABLE coin_aggregate (id serial,
coin_id varchar,
date_month int,
date_year int,
max_val float,
min_val float
);


CREATE TABLE coin_price (
    id serial PRIMARY KEY,
    coin_id varchar(20),
    price float(20),
    date_request date,
    response jsonb,
    CONSTRAINT coin_price_unique_constraint UNIQUE (coin_id, date_request)
);