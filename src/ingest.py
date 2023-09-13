import requests
import json
from datetime import datetime, timedelta
import argparse
from sqlalchemy import create_engine, text
import logging

logging.basicConfig(level=logging.debug==True)


def download_data(date:datetime, coin_id:str)->json:
    """Download data from AIP coingecko.

    :param date: date to request
    :type date: datetime
    :param coin_id: coin to request (bitcoin, ether, other)
    :type coin_id: str
    :return: data witout processing from API
    :rtype: json
    """
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/history?date={date.strftime('%d-%m-%Y')}"
    logging.info(f"Processing date: {date.strftime('%d-%m-%Y')}")
    logging.info(f"Get data from: {url}")
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        logging.info("Data recieve OK")
        return data
    else:
        logging.debug(f"Failed to fetch data for {date}. Status code: {response.status_code}")
        return None

def save_data_to_file(coin_id:str, date_list:list[datetime])->None:
    """Save raw data locally.

    :param coin_id:coin to request (bitcoin, ether, other)
    :type coin_id: str
    :param date_list: A list of date processed by main, can contain from 1 to n date
    :type date_list: list[datetime]
    """
    for date in date_list:
        data = download_data(date, coin_id)
        filename = f"{date.strftime('%d-%m-%Y')}_data.json"
        logging.info(f"Saving {filename}")
        with open(filename, "w") as file:
            json.dump(data, file, indent=4)
            logging.info(f"Data saved to {filename}")

def get_coin_data(data:json, date:datetime)->str:
    """Generate a query to insert into table.

    :param data: Raw data from API
    :type coin_id: json
    :param date: date related to the data requested
    :type date: datetime
    :return: query as a string to insert data in database
    :rtype: str
    """
    table_coin = "coin_price"
    id_val = data['id']
    price_usd = data['market_data']['current_price']['usd']
    data_json = json.dumps({"data":data})

    string_insert = f"""INSERT INTO {table_coin} (coin_id, price, date_request,response)
    VALUES ('{id_val}',{price_usd} ,'{date.strftime("%Y-%m-%d")}','{data_json}')
    ON CONFLICT (coin_id, date_request) DO UPDATE
    SET price = EXCLUDED.price, response = EXCLUDED.response;;"""

    return string_insert

def get_connection()->create_engine:
    """Create a connection using sqlalchemy.
    :return: return a connection ready to use
    :rtype: create_engine
    """

    db_usr = "postgres"
    db_password = "postgres"
    db_host = "localhost"
    db_name = "database_mutt"
    db_port = "5432"
    try:
        db_con = f'postgresql://{db_usr}:{db_password}@{db_host}:{db_port}/{db_name}'
        db = create_engine(db_con)
    except Exception as ex:
        logging.debug(ex)
    return db

def save_data_to_database(coin_id:str, date_list:list[datetime])->None:
    """Save process data in database.

    :param coin_id:coin to request (bitcoin, ether, other)
    :type coin_id: str
    :param date_list: A list of date processed by main, can contain from 1 to n date
    :type date_list: list[datetime]
    """
    for date in date_list:
        data = download_data(date, coin_id)
        try:
            db=get_connection()
            query = get_coin_data(data,date).replace("\n","")
            with db.connect() as con:
                res = con.execute(text(query))
                #con.commit()
                logging.debug(res)

        except Exception as ex:
            logging.debug(ex)
        update_agg(coin_id, date.month, date.year)

def update_agg(coin_id:str,month:int,year:int)->None:
    """Update price and respose in table when a combination of coin_id, month and year already exist.

    :param coin_id:coin to request (bitcoin, ether, other)
    :type coin_id: str
    :param month: month to update
    :type month: int
    :param year: year to update
    :type year: int
    """
    db = get_connection()
    query = f"""select min(price), max(price) from coin_price cp where extract(month from date_request)={month}
    and extract(year from date_request)={year}
    and coin_id='{coin_id}';"""

    with db.connect() as con:
            data = con.execute(text(query))
            logging.debug(data)
            result = data.fetchall()
            min = result[0][0]
            max = result[0][1]

    query = f"""select id from coin_aggregate where date_month={month}
    and date_year={year}
    and coin_id='{coin_id}';"""
    db = get_connection()
    with db.connect() as con:
            data = con.execute(text(query))
            logging.debug(data)
            result = data.fetchall()
            if result:
                 id_coin_agg = result[0][0]
                 query = f"""UPDATE coin_aggregate SET min_val = {min}, max_val ={max} where id={id_coin_agg};"""
                 with db.connect() as con:
                    data = con.execute(text(query)).rowcount
                    logging.info("Data updated")
            else:
                query = f"""INSERT INTO coin_aggregate (coin_id, date_month, date_year, max_val, min_val)
                            VALUES ('{coin_id}',{month},{year},{max},{min})"""
                with db.connect() as con:
                        data = con.execute(text(query)).rowcount
                        #con.commit()
                        logging.info("Data inserted")

def main():
    parser = argparse.ArgumentParser(description="Download and save coin data for a specific date.")
    parser.add_argument("coin_id", help="Coin identifier (e.g., bitcoin)")
    parser.add_argument("--start_date", help="ISO8601 date (YYYY-MM-DD)")
    parser.add_argument("--end_date", help="ISO8601 date (YYYY-MM-DD)")
    parser.add_argument("--save_option", default='database', help="save_option (database or local)")

    args = parser.parse_args()
    if args.start_date:
            start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    else:
        # Get the current date
        current_date = datetime.now()
        # Format the date as YYYY-MM-DD
        formatted_date = current_date.strftime("%Y-%m-%d")
        start_date = datetime.strptime(formatted_date, '%Y-%m-%d')
    if args.end_date:
        end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

        days_list = [(start_date + timedelta(days=i)) for i in range((end_date - start_date).days + 1)]

    else:
        days_list=[start_date]
    try:
        if args.save_option=='local':
            logging.warning("Working in local mode")
            save_data_to_file(args.coin_id, days_list)
        if args.save_option=='database':
            logging.warning("Working in database mode")
            save_data_to_database(args.coin_id, days_list)

    except ValueError:
        logging.warning("Invalid date format. Please use YYYY-MM-DD.")

if __name__ == "__main__":
    main()