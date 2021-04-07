# Importamos los modulos para web scraping
import requests
from bs4 import BeautifulSoup
# Módulos para manipulación de datos
import pandas as pd
# Módulo para expresiones regulares
import re
# Módulo para gestión de ficheros
import os
# Módulo para timing
from datetime import datetime
# Módulo para leer ficheros json
import json
# Módulo para tratamiento de arrays
import numpy as np


# URL
# Para hacer la petición tenemos que informar al website que somos un navegador
# y para ello usamos la variable 'headers'
url = 'https://www.transfermarkt.es/laliga/marktwerte/wettbewerb/ES1/plus//galerie/0?pos=&detailpos=&altersklasse=alle'
headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36'}
page = requests.get(url, headers=headers)
# Wrangling HTML with BeautifulSoup
# El objeto BeautifulSoup lo utilizaremos para la extracción de datos
# The 'html.parser' parameter represents which parser we will use when creating our object,
# a parser is a software responsible for converting an entry to a data structure.
pagina_bs = BeautifulSoup(page.content, 'html.parser')

# Obtención de los nombres de los jugadores
nombres_jugadores = []
# The find_all () method is able to return all tags that meet restrictions within parentheses
tags_jugadores = pagina_bs.find_all("a", {"class": "spielprofil_tooltip"})
# In our case, we are finding all anchors with the class "spielprofil_tooltip"

# Obtenemos tan solo el nombre
for tag_jugador in tags_jugadores:
    nombres_jugadores.append(tag_jugador.text)

# Obtenemos el precio de los jugadores
precio_jugadores = []

tags_precios = pagina_bs.find_all("td", {"class": "rechts hauptlink"})

for tag_precio in tags_precios:
    texto_precio = tag_precio.text
    # The price text contains characters that we don’t need like (euros) and m (million) so we’ll remove them
    texto_precio = texto_precio.replace("€", "").replace("mill.","").replace(",00","")
    # We will now convert the value to a numeric variable (float)
    precio_numerico = float(texto_precio)
    precio_jugadores.append(precio_numerico)

# Equilibramos número de datos
total_datos_validos = min(len(nombres_jugadores), len(precio_jugadores))
nombres_jugadores = nombres_jugadores[0:total_datos_validos]
precio_jugadores = precio_jugadores[0:total_datos_validos]

# Ahora creamos un DataFrame con Pandas
df = pd.DataFrame({
    'Jugador': nombres_jugadores,
    'Precio (millones de euros)': precio_jugadores
})

print(df)