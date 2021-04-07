from airflow.models import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from airflow.providers.http.sensors.http import HttpSensor
from airflow.providers.http.operators.http import SimpleHttpOperator
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

from datetime import datetime
from pandas import json_normalize
import json

# Definimos los default_arguments
default_args = {
    'start_date': datetime(2021, 1, 1)
}

# Esta función es invocada por un PythonOperator
# Recibirá como parámetro un task_instance
# Cuando una tarea es lanzada por el scheduler, es posible acceder al objeto
# task_instance. Y a partir de este objeto, será posible acceder a los xcoms
# Los xcoms es la forma de intercambiar datos entre distintas tareas.
def _processing_user(ti):
    users = ti.xcom_pull(task_ids=['extracting_user'])
    if not len(users) or 'results' not in users[0]:
        raise ValueError('User is empty')
    user = users[0]['results'][0]
    processed_user = {
        'firstname': user['name']['first'],
        'lastname': user['name']['last'],
        'country': user['location']['country'],
        'username': user['login']['username'],
        'password': user['login']['password'],
        'email': user['email']
    }
    # Convertimos este diccionario a un dataframe usando pandas y json_normalize
    processed_user = json_normalize(processed_user)
    # Esto nos facilitará almacenar el json en un fichero csv para que
    # sea utilizado por la siguiente tarea
    processed_user.to_csv('/tmp/processed_user.csv', index=None, header=False)



# Definimos el dag_id, el intervalo de ejecución y el start_date
with DAG('user_processing', schedule_interval='@daily',
        default_args=default_args,
        catchup=True) as dag:

    # Definimos las tasks/operators
    creating_table = SqliteOperator(
        task_id='creating_table',
        sqlite_conn_id='db_sqlite',
        sql='''
            CREATE TABLE IF NOT EXISTS users (
                firstname TEXT NOT NULL,
                lastname TEXT NOT NULL,
                country TEXT NOT NULL,
                username TEXT NOT NULL,
                password TEXT NOT NULL,
                email TEXT NOT NULL PRIMARY KEY
            );
            '''
    )

    # HTTP Sensor
    is_api_available = HttpSensor(
        task_id='is_api_available',
        http_conn_id='user_api',
        endpoint='api/'
    )

    # Operator para descargar datos del API
    extracting_user = SimpleHttpOperator(
        task_id='extracting_user',
        http_conn_id='user_api',
        endpoint='api',
        method='GET',
        response_filter=lambda response: json.loads(response.text),
        log_response=True
    )

    # Processing users
    processing_user = PythonOperator(
        task_id='processing_user',
        python_callable=_processing_user
    )

    # Ahora queremos almacenar el usuario que está en csv en la base de datos
    # Para ello vamos a utilizar el bash_operator. Nos permitirá ejecutar
    # comandos bash.
    storing_user = BashOperator(
        task_id='storing_user',
        bash_command='echo -e ".separator ","\n.import /tmp/processed_user.csv users" | sqlite3 /home/jcla/airflow/airflow.db'
    )

    # Establezcamos las dependencias
    creating_table >> is_api_available >> extracting_user >> processing_user >> storing_user
