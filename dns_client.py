import grpc
import dns_pb2
import dns_pb2_grpc

def query_dns(domain):
    with grpc.insecure_channel('grpc-server:50051') as channel:
        stub = dns_pb2_grpc.DNSServiceStub(channel)
        response = stub.GetDNS(dns_pb2.DNSRequest(domain=domain))
        return list(response.ips)
