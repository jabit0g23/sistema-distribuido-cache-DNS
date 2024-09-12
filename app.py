from flask import Flask, jsonify, request
from rediscluster import RedisCluster
import subprocess
import threading
from werkzeug.serving import make_server

app = Flask(__name__)

# Función para obtener los nodos de Redis desde los contenedores Docker
def get_redis_nodes():
    nodes = []
    # Nombres de los contenedores Redis, según tu docker-compose
    redis_containers = ['redis-server-1', 'redis-server-2', 'redis-server-3']
    
    for container in redis_containers:
        try:
            # Ejecuta el comando docker inspect para obtener la IP del contenedor
            result = subprocess.run(
                ['docker', 'inspect', container, '--format', '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'],
                capture_output=True,
                text=True,
                check=True
            )
            ip = result.stdout.strip()
            if ip:
                nodes.append({"host": ip, "port": "6379"})
        except subprocess.CalledProcessError as e:
            print(f"Error al obtener IP para {container}: {e}")
    
    return nodes

# Obtener los nodos de Redis automáticamente
startup_nodes = get_redis_nodes()
print("Nodos detectados:", startup_nodes)  # Verifica los nodos obtenidos

# Conexión al clúster de Redis
cache = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

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
