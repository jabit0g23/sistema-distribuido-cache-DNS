import requests
import random
import pandas as pd
import time

# Define la URL de la API Flask
api_url = 'http://localhost:5001/dns'

# Lee las primeras filas para determinar el tamaño del archivo sin cargarlo completamente en memoria
row_count = sum(1 for row in open('3rd_lev_domains_sample.csv'))  # No restamos porque no hay encabezado

# Ajusta el tamaño de la muestra para que no exceda el número total de filas
sample_size = min(20000, row_count)

# Lee una muestra aleatoria de filas desde el archivo CSV sin encabezado y asigna un nombre a la columna
domains_df = pd.read_csv('3rd_lev_domains_sample.csv', header=None, names=['domain'])

# Toma una muestra aleatoria de los dominios
domains_sample = domains_df.sample(n=sample_size, random_state=1).reset_index(drop=True)

# Asigna un ID a cada dominio
domains_sample['id'] = domains_sample.index + 1

# Almacena los dominios en un diccionario para un acceso rápido por ID
domains_dict = domains_sample.set_index('id')['domain'].to_dict()

# Función para realizar consultas a la API con un dominio aleatorio basado en un ID aleatorio
def query_random_domain():
    random_id = random.randint(1, sample_size)
    domain = domains_dict[random_id]
    try:
        response = requests.get(api_url, params={'domain': domain})
        data = response.json()
        print(f"Request to {domain}: {data}")
    except requests.exceptions.RequestException as e:
        print(f"Error requesting {domain}: {e}")

# Consulta aleatoria en un bucle infinito con un tiempo de espera ajustable
while True:
    query_random_domain()
    time.sleep(0.1)  # Ajusta el tiempo de espera entre solicitudes si es necesario
