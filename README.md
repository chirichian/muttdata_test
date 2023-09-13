# exam-rodrigo-chirichian
The follow description going to help you to setup the environment.

into src is ingest.py and the requirement.txt file to excecute the process
1 - install all the requirements
2 - run the docker-compose = docker-compose up
    The configuration file is into database_mutt in database.env
** If you don't have the postgres image run in terminal: docker pull postgres
How to execute ingest.py? ingest.py recieve 4 differents parameters:
    coin_id = (bitcoin, ethereum, cardano)
    as optional:
    start_date = (YYYY-MM-DD) ex: 2023-08-01
    end_date = (YYYY-MM-DD) ex: 2023-08-01, this option let you process many date. If there isn't end_date the process only get start_date
    save_option = as default database, but can choose local. The first save data into postgres the second one save data in the current path

Example:
python3 ingest.py cardano 2023-08-01 --end_date=2023-08-10 -> ingest cardano data from 2023-08-01 to 2023-08-10

python3 ingest.py cardano 2023-08-01 -> ingest cardano data 2023-08-01

## Crontab
To configure a crontab will run the app every day at 3am for the identifiers bitcoin, ethereum and cardano.
Open terminal:
execute:
contab -e
and add into the cron:
0 3 * * * /usr/bin/python3 /exam-rodrigo-chirichian/src/ingest.py bitcoin
0 3 * * * /usr/bin/python3 /exam-rodrigo-chirichian/src/ingest.py cardano
0 3 * * * /usr/bin/python3 /exam-rodrigo-chirichian/src/ingest.py ethereum

# Airflow
Incompleted, I couldn't configure docker airflow using my current postgres database