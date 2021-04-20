from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.subdag import SubDagOperator
from airflow.utils.task_group import TaskGroup
from airflow.operators.dummy import DummyOperator

from random import uniform
from datetime import datetime

default_args = {
    'start_date': datetime(2021, 1, 1)
}

def _training_model(ti):
    accuracy = uniform(0.1, 10.0)
    print(f'model\'s accuracy: {accuracy}')
    ti.xcom_push(key='model_accuracy', value=accuracy)

def _choose_best_model(ti):
    print('choose best model')
    accuracies = ti.xcom_pull(key='model_accuracy', task_ids=[
        'processing_tasks.training_model_a',
        'processing_tasks.training_model_b',
        'processing_tasks.training_model_c',
    ])
    # Aquí tenemos que devolver el task_id de la tarea que queremos ejecutar
    for accuracy in accuracies:
        if accuracy > 5:
            return 'accurate'
    return 'inaccurate'
    # Es posible devolver una lista con varias tareas a ejecutar
    # return ['accurate', 'inaccurate']


with DAG('xcom_dag', schedule_interval='@daily', default_args=default_args, catchup=False) as dag:

    downloading_data = BashOperator(
        task_id='downloading_data',
        bash_command='sleep 3'
    )
    # Algunos operators por defecto utilizan XCom. BashOperator es uno de ellos
    # Si quisiéramos modificar este comportamiento, deberíamos hacer:
    # downloading_data = BashOperator(
    #     task_id='downloading_data',
    #     bash_command='sleep 3',
    #     do_xcom_push=False
    # )

    with TaskGroup('processing_tasks') as processing_tasks:
        training_model_a = PythonOperator(
            task_id='training_model_a',
            python_callable=_training_model
        )

        training_model_b = PythonOperator(
            task_id='training_model_b',
            python_callable=_training_model
        )

        training_model_c = PythonOperator(
            task_id='training_model_c',
            python_callable=_training_model
        )

    choose_model = BranchPythonOperator(
        task_id='choose_best_model',
        python_callable=_choose_best_model
    )

    accurate = DummyOperator(
        task_id='accurate'
    )

    inaccurate = DummyOperator(
        task_id='inaccurate'
    )

    storing = DummyOperator(
        task_id='storing',
        trigger_rule='none_failed_or_skipped'
    )

    downloading_data >> processing_tasks >> choose_model
    choose_model >> [accurate, inaccurate] >> storing
    # Por defecto, la tarea 'storing' no se ejecutará si las dos tareas
    # que la preceden no se ejecutaron. ¿Cómo cambiar este comportamiento por defecto?
    # Imaginemos que quiero ejecutar una tarea 'Alerting' que quiero que se ejecute
    # si alguna de las tareas anteriores finalizó con error