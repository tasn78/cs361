# endpoint_client.py
import socket
import json
import uuid
import platform
import psutil
import time
from datetime import datetime

class EndpointClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.endpoint_id = str(uuid.uuid4())
        
    def get_system_info(self):
        return {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def send_heartbeat(self):
        data = {
            'id': self.endpoint_id,
            'hostname': platform.node(),
            'ip': socket.gethostbyname(socket.gethostname()),
            'system_info': self.get_system_info()
        }
        
        try:
            client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client.connect((self.server_host, self.server_port))
            client.send(json.dumps(data).encode())
            client.close()
        except Exception as e:
            print(f"Error sending heartbeat: {e}")

if __name__ == '__main__':
    client = EndpointClient('localhost', 5000)
    while True:
        client.send_heartbeat()
        time.sleep(60)  # Send heartbeat every minute