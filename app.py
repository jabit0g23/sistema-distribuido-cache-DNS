from flask import Flask, jsonify, request
from rediscluster import RedisCluster
import subprocess
import threading
from werkzeug.serving import make_server

app = Flask(__name__)

# Configura la conexión al clúster Redis
startup_nodes = [
    {"host": "192.168.0.2", "port": "6379"},
    {"host": "192.168.0.3", "port": "6379"},
    {"host": "192.168.0.4", "port": "6379"},
]

# Verificar la lista de nodos antes de conectar
startup_nodes = get_redis_nodes()
print("Nodos detectados:", startup_nodes)


# Conexión al clúster de Redis
cache = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

# Configuración para alternar entre particionamiento por hash o por rango
partition_mode = 'hash'  # Cambia a 'range' para particionamiento por rango

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
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain is required"}), 400

    # Verifica si el dominio está en el caché
    cached_result = cache.get(domain)
    source = "cache" if cached_result else "no cache"

    if cached_result:
        result = cached_result.split(', ')
    else:
        result = dig_query_no_cache(domain)
        cache.set(domain, ', '.join(result))  # Almacena en caché

    return jsonify({
        "domain": domain,
        "IP": result,
        "source": source
    }), 200 if result else 404

if __name__ == '__main__':
    server = ServerThread(app)
    server.start()