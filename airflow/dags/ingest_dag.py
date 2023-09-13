from airflow.models import DAG
from airflow.operators.python_operator import PythonOperator
from airflow.operators.dummy import DumyOperator
from datetime import datetime

#Definition of DAG
with DAG(
    dag_id = 'download_data',
    start_date = datetime(2023,22,1)
    schedule_interval = '@daily'
) as dag:

    init_process = DumyOperator(
        task_id = 'start_process'
    )

    download_data =PythonOperator(
        
    ) 
