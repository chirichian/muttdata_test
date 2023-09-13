
--Get the average price for each coin by month.
select
	coin_id,
	  extract(month
from
	date_request)as month,
	extract(year
from
	date_request)as year,
	avg(price)
from
	coin_price cp
group by
	coin_id,
	extract(month
from
	date_request),
	extract(year
from
	date_request);


--Calculate for each coin, on average, how much its price has increased after it had
--dropped consecutively for more than 3 days. In the same result set include the
--current market cap in USD (obtainable from the JSON-typed column). Use any time
--span that you find best.

with consecutive_drops as (
select
	id,
	coin_id,
	price,
	date_request,
	response->'data'->'market_data'->'market_cap'->>'usd'  as market_cap,
	lag(price,
	1) over (partition by coin_id
order by
	date_request) as prev_price,
	case
		when price > lag(price,
		1) over (partition by coin_id
	order by
		date_request) then 0
		else 1
	end as result
from
	coin_price
)
,
reset_flags as (
select
	id,
	coin_id,
	price,
	date_request,
	market_cap,
	prev_price,
	result,
	case
		when result = 0 then 1
		else 0
	end as reset_flag
from
	consecutive_drops
)
,
reset_positions as (
select
	id,
	coin_id,
	price,
	date_request,
	market_cap,
	prev_price,
	result,
	reset_flag,
	SUM(reset_flag) over (partition by coin_id
order by
	date_request) as reset_position
from
	reset_flags
)
,
final_result as(
select
	id,
	coin_id,
	price,
	date_request,
	market_cap,
	prev_price,
	result,
	lead(price) over (partition by coin_id order by date_request) - price as increase_price,
	SUM(result) over (partition by coin_id,
	reset_position
order by
	date_request) as cumulative_sum,
	lead(result,
	1) over (partition by coin_id
order by
	date_request) as post_result
from
	reset_positions
)select
	coin_id,
	max(market_cap),
	avg(increase_price) as avg_price
from
	final_result
where
	cumulative_sum >= 3
	and post_result = 0
group by
	coin_id
order by
	coin_id;