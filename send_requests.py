import requests
import random
import pandas as pd
import time
import matplotlib.pyplot as plt
import numpy as np

# Define la URL de la API Flask
api_url = "http://localhost:5001/dns"

# Lee las primeras filas para determinar el tamaño del archivo sin cargarlo completamente en memoria
row_count = sum(1 for row in open('3rd_lev_domains_sample.csv'))

# Ajusta el tamaño de la muestra para que no exceda el número total de filas
sample_size = min(20000, row_count)

# Lee una muestra aleatoria de filas desde el archivo CSV sin encabezado y asigna un nombre a la columna
domains_df = pd.read_csv('3rd_lev_domains_sample.csv', header=None, names=['domain'])

# Toma una muestra aleatoria de los dominios
domains_sample = domains_df.sample(n=sample_size, random_state=1).reset_index(drop=True)

# Almacena los dominios en un diccionario para un acceso rápido por ID
domains_dict = domains_sample['domain'].to_dict()

# Diccionario para rastrear las peticiones por nodo
node_requests = {}

# Función para realizar consultas a la API y medir estadísticas
def query_domain(domain):
    try:
        start_time = time.time()
        response = requests.get(api_url, params={'domain': domain})
        response.raise_for_status()
        end_time = time.time()
        data = response.json()
        is_hit = data['source'] == 'cache'
        
        # Obtener el nodo real desde la respuesta de la API
        node = data.get('node', 'Unknown Node')
        node_requests[node] = node_requests.get(node, 0) + 1
        
        return {
            'data': data,
            'time': (end_time - start_time) * 1000,  # Convertimos el tiempo a milisegundos
            'hit': is_hit,
            'node': node
        }
    except requests.RequestException as e:
        print(f"Error al solicitar {domain}: {e}")
        return None

def main():
    hits_times = []
    misses_times = []
    response_source = {}

    for _ in range(500):  # Número de solicitudes que deseas realizar
        domain = domains_dict[random.randint(0, sample_size - 1)]
        result = query_domain(domain)

        if result:
            source = result['data']['source']
            response_source[source] = response_source.get(source, 0) + 1
            if result['hit']:
                hits_times.append(result['time'])
            else:
                misses_times.append(result['time'])

    # Calcular estadísticas para tiempos de respuesta
    hit_avg_time = np.mean(hits_times) if hits_times else 0
    hit_std_dev = np.std(hits_times, ddof=1) if hits_times else 0  # Ajuste aquí
    miss_avg_time = np.mean(misses_times) if misses_times else 0
    miss_std_dev = np.std(misses_times, ddof=1) if misses_times else 0  # Ajuste aquí

    # Imprimir estadísticas
    print(f"Cache hits: {len(hits_times)}")
    print(f"Cache misses: {len(misses_times)}")
    print(f"Cache hit average time: {hit_avg_time:.2f} ms")
    print(f"Cache miss average time: {miss_avg_time:.2f} ms")
    print(f"Response sources: {response_source}")

    # Imprimir balance de carga por nodo
    print("Load balance per partition:")
    for node, count in node_requests.items():
        print(f"{node}: {count} requests")

    # Graficar resultados con promedios y desviaciones estándar
    plt.figure(figsize=(10, 6))

    # Gráfico de barras para tiempos promedio y desviación estándar
    categories = ['Cache Hits', 'Cache Misses']
    averages = [hit_avg_time, miss_avg_time]
    std_devs = [hit_std_dev, miss_std_dev]

    bars = plt.bar(categories, averages, yerr=std_devs, capsize=5, color=['green', 'red'], alpha=0.7)
    plt.title('Average Response Times with Standard Deviation')
    plt.xlabel('Response Type')
    plt.ylabel('Time (ms)')

    # Añadir texto con los valores de promedio y desviación estándar sobre las barras
    for bar, avg, std in zip(bars, averages, std_devs):
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + std + 10, f'{avg:.2f} ms\n±{std:.2f}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('average_response_times.png')  # Guardar gráfico
    print("Gráfico de tiempos de respuesta promedio guardado como 'average_response_times.png'")

    # Gráfico de conteo de hits vs misses
    plt.figure(figsize=(7, 5))
    plt.bar(['Cache Hits', 'Cache Misses'], [len(hits_times), len(misses_times)], color=['green', 'red'])
    plt.title('Number of Cache Hits vs Misses')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig('hits_vs_misses.png')  # Guardar gráfico
    print("Gráfico de hits vs misses guardado como 'hits_vs_misses.png'")

    # Gráfico de balance de carga por partición
    plt.figure(figsize=(10, 6))
    plt.bar(node_requests.keys(), node_requests.values(), color='blue', alpha=0.7)
    plt.title('Load Balance per Partition')
    plt.xlabel('Partition (Node)')
    plt.ylabel('Number of Requests')
    plt.tight_layout()
    plt.savefig('load_balance_per_partition.png')  # Guardar gráfico
    print("Gráfico de balance de carga por partición guardado como 'load_balance_per_partition.png'")

if __name__ == "__main__":
    main()
