# dns_server.py
from concurrent import futures
import grpc
import subprocess
import dns_pb2
import dns_pb2_grpc

class DNSService(dns_pb2_grpc.DNSServiceServicer):
    def GetDNS(self, request, context):
        domain = request.domain
        try:
            # Ejecuta el comando `dig` desde la consola de Linux
            result = subprocess.run(['dig', '+short', domain], capture_output=True, text=True, check=True)
            output = result.stdout.strip()
            ips = [line for line in output.splitlines() if line]
            # Devuelve las IPs encontradas como lista
            return dns_pb2.DNSResponse(ips=ips if ips else ["No IP found"])
        except subprocess.CalledProcessError as e:
            # Error al ejecutar el comando `dig`
            return dns_pb2.DNSResponse(ips=[f"Error: {e}"])
        except Exception as e:
            # Manejo de cualquier otro error
            return dns_pb2.DNSResponse(ips=[f"Exception: {str(e)}"])

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    dns_pb2_grpc.add_DNSServiceServicer_to_server(DNSService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    print("gRPC Server is running on port 50051...")
    server.wait_for_termination()

if __name__ == '__main__':
    serve()
