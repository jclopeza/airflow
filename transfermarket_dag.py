from airflow.models import DAG
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.operators.python import PythonOperator

# Importamos los modulos para web scraping
import requests
from bs4 import BeautifulSoup
import pandas as pd

from datetime import datetime


# Definimos los default_arguments
default_args = {
    'start_date': datetime(2021, 1, 1)
}


def _getting_html_page(ti):
    # URL: Para hacer la petición tenemos que informar al website
    # que somos un navegador y para ello usamos la variable 'headers'
    url = 'https://www.transfermarkt.es/laliga/marktwerte/wettbewerb/ES1/plus//galerie/0?pos=&detailpos=&altersklasse=alle'
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'}
    page = requests.get(url, headers=headers)
    ti.xcom_push(key='transfermarkt_raw_html', value=page.text)

def _processing_players(ti):
    transfermarkt_raw_html = ti.xcom_pull(key='transfermarkt_raw_html', task_ids=['getting_html_page'])
    page_bs = BeautifulSoup(str(transfermarkt_raw_html), 'html.parser')
    players_name = []
    players_price = []
    players_tags = page_bs.find_all("a", {"class": "spielprofil_tooltip"})
    prices_tags = page_bs.find_all("td", {"class": "rechts hauptlink"})
    for player_tag in players_tags:
        players_name.append(player_tag.text)
    for price_tag in prices_tags:
        players_price.append(price_tag.text)
    # Equilibramos datos, se devuelve el primer nombre duplicado
    total_valid_data = min(len(players_name), len(players_price))
    players_name = players_name[0:total_valid_data]
    players_price = players_price[0:total_valid_data]
    # Ahora creamos un DataFrame con Pandas
    df = pd.DataFrame({
        'Jugador': players_name,
        'Precio (millones de euros)': players_price
    })
    df.to_csv('/tmp/players_and_prices.csv', index=False, header=False)


# Definimos el DAG
with DAG('transfermarkt_processing', schedule_interval='@daily',
        default_args=default_args,
        catchup=False) as dag:

    # Definimos las tasks/operators
    creating_table = PostgresOperator(
        task_id='creating_table',
        postgres_conn_id='transfermarkt',
        sql=['DROP TABLE IF EXISTS players',
            'CREATE TABLE players (name TEXT NOT NULL, price TEXT NOT NULL)']
    )

    # Descargando la página HTML
    getting_html_page = PythonOperator(
        task_id='getting_html_page',
        python_callable=_getting_html_page
    )

    # Procesamiento de jugadores
    processing_players = PythonOperator(
        task_id='processing_players',
        python_callable=_processing_players
    )

    creating_table >> getting_html_page >> processing_players
