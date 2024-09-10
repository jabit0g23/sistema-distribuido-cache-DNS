from flask import Flask, jsonify, request
from rediscluster import RedisCluster
import subprocess

app = Flask(__name__)

# Configura la conexión al clúster Redis
startup_nodes = [
    {"host": "192.168.16.2", "port": "6379"},
    {"host": "192.168.16.3", "port": "6379"},
    {"host": "192.168.16.4", "port": "6379"},
]

# Conexión al clúster de Redis
cache = RedisCluster(startup_nodes=startup_nodes, decode_responses=True)

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
    if cached_result:
        return jsonify({
            "domain": domain,
            "IP": cached_result.split(', '),
            "source": "cache"
        }), 200

    # Si no está en caché, consulta con dig sin caché y almacena el resultado
    result = dig_query_no_cache(domain)
    cache.set(domain, ', '.join(result))  # Almacena en caché

    return jsonify({
        "domain": domain,
        "IP": result,
        "source": "no cache"
    }), 200 if result else 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
