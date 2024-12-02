import socket
import json
import uuid
import random
import time
from datetime import datetime
import ssl

class EndpointClient:
    def __init__(self, server_host='127.0.0.1', server_port=5000):
        self.server_host = server_host
        self.server_port = server_port
        self.endpoint_id = str(uuid.uuid4())
        self.device_types = ['laptop', 'desktop', 'workstation', 'server']
        self.device_name = f"{random.choice(self.device_types)}-{random.randint(100,999)}"

    def get_system_info(self):
        return {
            'platform': random.choice(['Windows', 'Linux', 'MacOS']),
            'cpu_percent': round(random.uniform(20, 95), 1),
            'memory_percent': round(random.uniform(30, 90), 1),
            'disk_usage': round(random.uniform(25, 85), 1),
            'timestamp': datetime.now().isoformat()
        }

    def send_heartbeat(self):
        data = {
            'id': self.endpoint_id,
            'hostname': self.device_name,
            'ip': f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}",
            'system_info': self.get_system_info(),
            'auth_key': "my_secure_shared_secret"  # Shared secret API key
        }
        try:
            # Set up SSL context for the client
            context = ssl.create_default_context(cafile='server.crt')  # Use the server's public certificate

            # Create a secure socket
            client = context.wrap_socket(
                socket.socket(socket.AF_INET, socket.SOCK_STREAM),
                server_hostname=self.server_host
            )
            client.connect((self.server_host, self.server_port))
            client.send(json.dumps(data).encode())
            client.close()
            print(f"Secure heartbeat sent for {self.device_name}")
        except Exception as e:
            print(f"Error sending secure heartbeat: {e}")

if __name__ == '__main__':
    client = EndpointClient()
    print(f"Starting endpoint client {client.device_name}")
    while True:
        client.send_heartbeat()
        time.sleep(5)