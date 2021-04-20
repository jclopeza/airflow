from airflow.models import DAG
from airflow.operators.bash import BashOperator

from datetime import datetime

# Definimos los default_arguments
default_args = {
    'start_date': datetime(2021, 1, 1)
}

# Definimos el dag_id, el intervalo de ejecución y el start_date
with DAG('trigger_rule', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    task_1 = BashOperator(
        task_id='task_1',
        bash_command='exit 1',
        do_xcom_push=False
    )

    task_2 = BashOperator(
        task_id='task_2',
        bash_command='sleep 30',
        do_xcom_push=False
    )

    task_3 = BashOperator(
        task_id='task_3',
        bash_command='exit 0',
        do_xcom_push=False,
        trigger_rule='one_failed'
    )

    [task_1, task_2] >> task_3