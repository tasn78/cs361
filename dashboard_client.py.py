# dashboard_server.py
from flask import Flask, render_template, jsonify
from datetime import datetime
import sqlite3
import threading
import socket
import json

class EndpointManager:
    def __init__(self, db_path='endpoints.db'):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS endpoints
                    (id TEXT PRIMARY KEY, hostname TEXT, ip TEXT, 
                     last_seen TIMESTAMP, status TEXT, system_info TEXT)''')
        conn.commit()
        conn.close()
    
    def update_endpoint(self, endpoint_id, hostname, ip, system_info):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''INSERT OR REPLACE INTO endpoints 
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (endpoint_id, hostname, ip, datetime.now(), 'online', system_info))
        conn.commit()
        conn.close()
    
    def get_all_endpoints(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT * FROM endpoints')
        endpoints = c.fetchall()
        conn.close()
        return endpoints

class CommunicationServer:
    def __init__(self, host='0.0.0.0', port=5000):
        self.host = host
        self.port = port
        self.endpoint_manager = EndpointManager()
        
    def start(self):
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((self.host, self.port))
        server.listen()
        
        while True:
            client, address = server.accept()
            client_handler = threading.Thread(target=self.handle_client, args=(client,))
            client_handler.start()
    
    def handle_client(self, client):
        try:
            data = client.recv(4096).decode()
            endpoint_data = json.loads(data)
            self.endpoint_manager.update_endpoint(
                endpoint_data['id'],
                endpoint_data['hostname'],
                endpoint_data['ip'],
                json.dumps(endpoint_data['system_info'])
            )
        except Exception as e:
            print(f"Error handling client: {e}")
        finally:
            client.close()
# dashboard_server.py
from flask import Flask, jsonify
from datetime import datetime
import sqlite3
import threading
import socket
import json

# [Keep your EndpointManager and CommunicationServer classes the same]

app = Flask(__name__)
endpoint_manager = EndpointManager()

@app.route('/')
def dashboard():
    endpoints = endpoint_manager.get_all_endpoints()
    return f"""
    <html>
        <head>
            <title>RMM Dashboard</title>
            <meta http-equiv="refresh" content="30">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                h1 {{ color: #333; }}
            </style>
        </head>
        <body>
            <h1>Endpoint Status Dashboard</h1>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Hostname</th>
                    <th>IP</th>
                    <th>Last Seen</th>
                    <th>Status</th>
                    <th>System Info</th>
                </tr>
                {''.join(f'''
                <tr>
                    <td>{endpoint[0]}</td>
                    <td>{endpoint[1]}</td>
                    <td>{endpoint[2]}</td>
                    <td>{endpoint[3]}</td>
                    <td>{endpoint[4]}</td>
                    <td>{endpoint[5]}</td>
                </tr>
                ''' for endpoint in endpoints)}
            </table>
        </body>
    </html>
    """

@app.route('/api/endpoints')
def get_endpoints():
    endpoints = endpoint_manager.get_all_endpoints()
    return jsonify(endpoints)

if __name__ == '__main__':
    # Start communication server in a separate thread
    comm_server = CommunicationServer()
    server_thread = threading.Thread(target=comm_server.start)
    server_thread.daemon = True
    server_thread.start()
    
    # Start web interface
    print("Starting web server on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=True)