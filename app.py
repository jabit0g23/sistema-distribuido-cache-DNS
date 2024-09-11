from flask import Flask, jsonify, request
from rediscluster import RedisCluster
import subprocess
import time
import threading
import statistics
from werkzeug.serving import make_server

app = Flask(__name__)

# Configura la conexión al clúster Redis
startup_nodes = [
    {"host": "172.31.0.3", "port": "6379"},
    {"host": "172.31.0.4", "port": "6379"},
    {"host": "172.31.0.5", "port": "6379"},
]

# Conexión al clúster de Redis
cache = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

# Variables para estadísticas
hits = 0
misses = 0
response_times = []
partition_requests = {"node1": 0, "node2": 0, "node3": 0}

# Configuración para alternar entre particionamiento por hash o por rango
partition_mode = 'hash'  # Cambia a 'range' para particionamiento por rango

# Clase para manejar el servidor Flask y permitir su cierre
class ServerThread(threading.Thread):
    def __init__(self, app):
        threading.Thread.__init__(self)
        self.server = make_server('0.0.0.0', 5001, app)
        self.ctx = app.app_context()
        self.ctx.push()

    def run(self):
        self.server.serve_forever()

    def shutdown(self):
        self.server.shutdown()

# Función para realizar la consulta DIG sin caché
def dig_query_no_cache(domain):
    try:
        result = subprocess.run(['dig', '+short', domain], capture_output=True, text=True)
        output = result.stdout.strip()
        ips = [line for line in output.splitlines() if line]
        return ips if ips else ["No IP found"]
    except Exception as e:
        return [str(e)]

@app.route('/dns', methods=['GET'])
def get_dns():
    global hits, misses, response_times
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    start_time = time.time()  # Tiempo de inicio

    # Verifica si el dominio está en el caché
    cached_result = cache.get(domain)
    if cached_result:
        hits += 1
        response_times.append(time.time() - start_time)  # Tiempo de respuesta
        # Actualiza el balance de carga según el nodo
        update_partition_load(domain)
        return jsonify({
            "domain": domain,
            "IP": cached_result.split(', '),
            "source": "cache"
        }), 200

    # Si no está en caché, consulta con dig sin caché y almacena el resultado
    result = dig_query_no_cache(domain)
    cache.set(domain, ', '.join(result))  # Almacena en caché
    misses += 1
    response_times.append(time.time() - start_time)  # Tiempo de respuesta

    # Actualiza el balance de carga según el nodo
    update_partition_load(domain)

    return jsonify({
        "domain": domain,
        "IP": result,
        "source": "no cache"
    }), 200 if result else 404

# Función para decidir el nodo basado en el modo de particionamiento
def get_node_by_key(key):
    if partition_mode == 'hash':
        # Uso del slot de Redis Cluster (hash)
        slot = int(cache.execute_command('CLUSTER', 'KEYSLOT', key))
        if slot >= 0 and slot <= 5460:
            return 'node1'
        elif slot >= 5461 and slot <= 10922:
            return 'node2'
        else:
            return 'node3'
    elif partition_mode == 'range':
        # Lógica personalizada de particionamiento por rango
        first_char = key[0].upper()  # Tomar la primera letra
        if 'A' <= first_char <= 'M':
            return 'node1'
        elif 'N' <= first_char <= 'Z':
            return 'node2'
        else:
            return 'node3'
    else:
        raise ValueError("Modo de particionamiento no soportado.")

# Modificación en la función de actualización de carga
def update_partition_load(key):
    global partition_requests
    try:
        node = get_node_by_key(key)
        partition_requests[node] += 1
    except Exception as e:
        print(f"Error updating partition load: {e}")

# Función para detener la ejecución después de un tiempo específico
def stop_after_timeout(timeout, server):
    time.sleep(timeout)
    print("\nEjecución detenida.")
    print(f"Hit Rate: {hits / (hits + misses) * 100:.2f}%")
    print(f"Miss Rate: {misses / (hits + misses) * 100:.2f}%")
    print(f"Tiempo de Respuesta Promedio: {statistics.mean(response_times):.4f} s")
    if len(response_times) > 1:
        print(f"Desviación Estándar del Tiempo de Respuesta: {statistics.stdev(response_times):.4f} s")
    else:
        print(f"Desviación Estándar del Tiempo de Respuesta: 0.0000 s")
    print(f"Balance de Carga: {partition_requests}")
    server.shutdown()

if __name__ == '__main__':
    server = ServerThread(app)
    server.start()
    timeout = 360  # Tiempo de ejecución en segundos
    threading.Thread(target=stop_after_timeout, args=(timeout, server)).start()
