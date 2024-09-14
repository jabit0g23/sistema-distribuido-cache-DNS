import requests
import random
import pandas as pd
import time
import matplotlib.pyplot as plt

# Define la URL de la API Flask, asegurándote de que coincida con el nombre del servicio en Docker Compose
api_url = "http://localhost:5001/dns"  # Usa localhost si corres localmente
  # Cambia 'api' por el nombre del servicio que usas en Docker Compose

# Lee las primeras filas para determinar el tamaño del archivo sin cargarlo completamente en memoria
row_count = sum(1 for row in open('3rd_lev_domains_sample.csv'))  # No restamos porque no hay encabezado

# Ajusta el tamaño de la muestra para que no exceda el número total de filas
sample_size = min(20000, row_count)

# Lee una muestra aleatoria de filas desde el archivo CSV sin encabezado y asigna un nombre a la columna
domains_df = pd.read_csv('3rd_lev_domains_sample.csv', header=None, names=['domain'])

# Toma una muestra aleatoria de los dominios
domains_sample = domains_df.sample(n=sample_size, random_state=1).reset_index(drop=True)

# Almacena los dominios en un diccionario para un acceso rápido por ID
domains_dict = domains_sample['domain'].to_dict()

# Función para realizar consultas a la API y medir estadísticas
def query_domain(domain):
    try:
        start_time = time.time()
        response = requests.get(api_url, params={'domain': domain})
        response.raise_for_status()
        end_time = time.time()
        data = response.json()
        is_hit = data['source'] == 'cache'
        return {
            'data': data,
            'time': (end_time - start_time) * 1000,  # Convertimos el tiempo a milisegundos
            'hit': is_hit
        }
    except requests.RequestException as e:
        print(f"Error al solicitar {domain}: {e}")
        return None

def main():
    hits_times = []
    misses_times = []
    response_source = {}

    for _ in range(1000):  # Número de solicitudes que deseas realizar
        domain = domains_dict[random.randint(0, sample_size - 1)]
        result = query_domain(domain)

        if result:
            source = result['data']['source']
            response_source[source] = response_source.get(source, 0) + 1
            if result['hit']:
                hits_times.append(result['time'])
            else:
                misses_times.append(result['time'])

    # Imprimir estadísticas
    print(f"Cache hits: {len(hits_times)}")
    print(f"Cache misses: {len(misses_times)}")
    print(f"Cache hit average time: {sum(hits_times) / len(hits_times) if hits_times else 0:.2f} ms")
    print(f"Cache miss average time: {sum(misses_times) / len(misses_times) if misses_times else 0:.2f} ms")
    print(f"Response sources: {response_source}")

    # Graficar los resultados
    plt.figure(figsize=(14, 7))

    # Gráfico de tiempos de respuesta
    plt.subplot(3, 1, 1)
    plt.scatter(range(len(hits_times)), hits_times, color='green', alpha=0.7, label='Cache Hits')
    plt.scatter(range(len(misses_times)), misses_times, color='red', alpha=0.7, label='Cache Misses')
    plt.title('Response Times for Cache Hits and Misses')
    plt.xlabel('Sample Number')
    plt.ylabel('Response Time (ms)')
    plt.legend()

    # Gráfico de conteo de hits vs misses
    plt.subplot(3, 1, 2)
    plt.bar(['Cache Hits', 'Cache Misses'], [len(hits_times), len(misses_times)], color=['green', 'red'])
    plt.title('Number of Cache Hits vs Misses')
    plt.ylabel('Count')

    # Gráfico de fuentes de respuesta
    plt.subplot(3, 1, 3)
    plt.bar(response_source.keys(), response_source.values(), color=['green', 'red', 'blue'], alpha=0.7)
    plt.title('Number of Responses by Source')
    plt.xlabel('Source')
    plt.ylabel('Responses')
    plt.tight_layout()

    plt.show()

if __name__ == "__main__":
    main()
