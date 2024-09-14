from flask import Flask, request, jsonify
from redis import Redis
import os
import grpc
from dns_pb2_grpc import DNSServiceStub
from dns_pb2 import DNSRequest

# Inicialización de la aplicación Flask
app = Flask(__name__)

# Obtener el tipo de particionado de la variable de entorno (hash por defecto)
PARTITION_TYPE = os.getenv('PARTITION_TYPE', 'hash').lower()  # Opciones: 'hash' o 'range'

def get_redis_nodes():
    # Obtiene los nodos de Redis desde la variable de entorno 'REDIS_NODES'
    nodes = os.getenv('REDIS_NODES', '').split(',')
    return [{"host": node.split(':')[0], "port": int(node.split(':')[1])} for node in nodes if node]

# Configuración de los nodos Redis usando la función anterior
redis_nodes = get_redis_nodes()

# Verificar si los nodos están configurados correctamente
if not redis_nodes:
    raise ValueError("No Redis nodes configured. Please check the REDIS_NODES environment variable.")

# Conectar a cada nodo de Redis y almacenarlos en un diccionario
redis_clients = {f"node_{i}": Redis(host=node["host"], port=node["port"], decode_responses=True)
                 for i, node in enumerate(redis_nodes)}

print("Connected to Redis nodes successfully.")

def query_dns_via_grpc(domain):
    # Conectar al servidor gRPC
    channel = grpc.insecure_channel('grpc-server:50051')  # Asegúrate de que este host y puerto sean correctos
    stub = DNSServiceStub(channel)
    try:
        # Llama al método GetDNS en el servidor gRPC
        response = stub.GetDNS(DNSRequest(domain=domain))
        # Convierte el resultado a una lista directamente
        return list(response.ips)
    except grpc.RpcError as e:
        print(f"gRPC Error: {e}")
        return ["Error fetching DNS record"]

def send_to_redis(domain, result):
    """
    Enviar datos a Redis usando el tipo de particionado seleccionado.
    """
    node_name = "unknown"
    try:
        if PARTITION_TYPE == 'hash':
            # Enviar usando particionado por hash
            node_client = select_node_by_hash(domain)
            node_client.set(domain, ', '.join(result))
            node_name = next((name for name, client in redis_clients.items() if client == node_client), "unknown")
            print(f"Data sent to Redis using hash partitioning to {node_name}.")
        elif PARTITION_TYPE == 'range':
            # Particionado por rango dinámico basado en el número de nodos disponibles
            slot = get_range_slot(domain)
            node_client = select_node_by_range(slot)
            node_client.set(domain, ', '.join(result))  # Enviar al nodo seleccionado
            node_name = next((name for name, client in redis_clients.items() if client == node_client), "unknown")
            print(f"Data sent to Redis using range partitioning to {node_name}.")
        else:
            print("Invalid partition type selected.")
    except Exception as e:
        print(f"Error sending data to Redis: {e}")
    
    return node_name


def get_range_slot(domain):
    """
    Simula un cálculo de slot basado en el rango de manera dinámica.
    """
    domain_value = sum(ord(char) for char in domain)  # Convierte el dominio a un valor numérico basado en sus caracteres
    total_slots = 16384  # Total de slots de Redis
    slot = domain_value % total_slots
    return slot

def select_node_by_range(slot):
    """
    Seleccionar el nodo de Redis basado en el slot de rango dinámicamente.
    """
    num_nodes = len(redis_clients)
    selected_node_index = slot % num_nodes  # Seleccionar el nodo basado en el slot y el número de nodos disponibles
    selected_node = redis_clients[f"node_{selected_node_index}"]
    return selected_node

def select_node_by_hash(domain):
    """
    Selecciona el nodo Redis usando particionado por hash.
    """
    hash_value = sum(ord(char) for char in domain)  # Simulación de hash básico basado en los caracteres del dominio
    num_nodes = len(redis_clients)
    selected_node_index = hash_value % num_nodes
    selected_node = redis_clients[f"node_{selected_node_index}"]
    return selected_node

@app.route('/dns', methods=['GET'])
def get_dns_record():
    domain = request.args.get('domain')
    if not domain:
        return jsonify({"error": "Domain parameter is missing"}), 400

    try:
        # Intenta obtener el registro desde los nodos Redis
        node_client = select_node_by_hash(domain) if PARTITION_TYPE == 'hash' else select_node_by_range(get_range_slot(domain))
        result = node_client.get(domain)
        if result:
            return jsonify({"domain": domain, "record": result, "source": "cache"}), 200

        # Si no está en caché, realiza una consulta DNS a través del servidor gRPC
        print(f"Record not found in cache for {domain}, querying gRPC server...")
        result = query_dns_via_grpc(domain)  # Llamada al gRPC server

        # Enviar los datos a Redis utilizando la lógica de particionado seleccionada
        selected_node = send_to_redis(domain, result)
        return jsonify({"domain": domain, "record": result, "source": "gRPC", "node": selected_node}), 200

    except Exception as e:
        print(f"Error fetching DNS record for {domain}: {e}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "API is running"}), 200

if __name__ == "__main__":
    # Iniciar la API Flask en el puerto 5001
    app.run(host="0.0.0.0", port=5001)
