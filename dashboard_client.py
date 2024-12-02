from flask import Flask
from datetime import datetime
import sqlite3
import threading
import socket
import json
import ssl


class EndpointManager:
    def __init__(self, db_path='endpoints.db'):
        self.db_path = db_path
        self._lock = threading.Lock()
        self.init_database()
        
    def init_database(self):
        with self._lock:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute('''CREATE TABLE IF NOT EXISTS endpoints
                        (id TEXT PRIMARY KEY, hostname TEXT, ip TEXT, 
                         last_seen TIMESTAMP, status TEXT, system_info TEXT)''')
            conn.commit()
            conn.close()
            print("\nDatabase initialized")
    
    def update_endpoint(self, endpoint_id, hostname, ip, system_info):
        with self._lock:
            try:
                print(f"\nAttempting database update")
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                now = datetime.now().isoformat()
                c.execute('''INSERT OR REPLACE INTO endpoints 
                            VALUES (?, ?, ?, ?, ?, ?)''',
                            (endpoint_id, hostname, ip, now, 'online', system_info))
                conn.commit()
                print(f"Updated endpoint in database: {hostname} with ID: {endpoint_id}")
                
                c.execute('SELECT * FROM endpoints WHERE id = ?', (endpoint_id,))
                result = c.fetchone()
                print(f"Verification - Record in DB: {result}")
                
                conn.close()
            except Exception as e:
                print(f"Database error: {e}")
    
    def get_all_endpoints(self):
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()
                
                c.execute('''UPDATE endpoints 
                            SET status = 'offline'
                            WHERE datetime(last_seen) < datetime('now', '-5 minutes')''')
                conn.commit()
                
                c.execute('SELECT * FROM endpoints')
                endpoints = c.fetchall()
                
                print("\nQuerying database contents:")
                for endpoint in endpoints:
                    print(f"ID: {endpoint[0]}, Hostname: {endpoint[1]}, Status: {endpoint[4]}")
                
                conn.close()
                return endpoints
            except Exception as e:
                print(f"Error getting endpoints: {e}")
                return []

    def deactivate_endpoint(self, endpoint_id):
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # Mark the endpoint as deactivated
                c.execute('''
                    UPDATE endpoints SET deactivated = 1 WHERE id = ?
                ''', (endpoint_id,))
                conn.commit()
                conn.close()
                print(f"Endpoint {endpoint_id} has been deactivated.")
            except Exception as e:
                print(f"Error deactivating endpoint: {e}")


# Updated to wrap its socket with SSL
class CommunicationServer:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.endpoint_manager = EndpointManager()

    def start(self):
        # Load SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='server.crt', keyfile='server.key')

        # Create socket and wrap with SSL
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self.host, self.port))
        server.listen()

        server = context.wrap_socket(server, server_side=True)  # Wrap the server socket
        print(f"\nCommunication server listening securely on {self.host}:{self.port}")

        while True:
            client, address = server.accept()
            print(f"\nSecure connection from {address}")
            client_handler = threading.Thread(target=self.handle_client, args=(client,))
            client_handler.start()

    def handle_client(self, client):
        try:
            data = client.recv(4096).decode()
            endpoint_data = json.loads(data)

            # Validate the shared secret
            if endpoint_data.get('auth_key') != "my_secure_shared_secret":
                print("Unauthorized client! Connection rejected.")
                client.close()
                return

            print(f"Authorized client: {endpoint_data['hostname']}")
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


    def deactivate_endpoint(self, endpoint_id):
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # Mark the endpoint as deactivated
                c.execute('''
                    UPDATE endpoints SET deactivated = 1 WHERE id = ?
                ''', (endpoint_id,))
                conn.commit()
                conn.close()
                print(f"Endpoint {endpoint_id} has been deactivated.")
            except Exception as e:
                print(f"Error deactivating endpoint: {e}")

    def reactivate_endpoint(self, endpoint_id):
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path)
                c = conn.cursor()

                # Mark the endpoint as active
                c.execute('''
                    UPDATE endpoints SET deactivated = 0 WHERE id = ?
                ''', (endpoint_id,))
                conn.commit()
                conn.close()
                print(f"Endpoint {endpoint_id} has been reactivated.")
            except Exception as e:
                print(f"Error reactivating endpoint: {e}")



app = Flask(__name__)
endpoint_manager = EndpointManager()


@app.route('/')
def dashboard():
    endpoints = endpoint_manager.get_all_endpoints()
    debug_info = f'''
        <div class="debug">
            <h2>Debug Info</h2>
            <p>Database Path: {endpoint_manager.db_path}</p>
            <p>Endpoints Count: {len(endpoints)}</p>
            <p>Last Refresh: {datetime.now().isoformat()}</p>
            <p>Server Status: Active</p>
        </div>
    '''

    rows = ''
    for endpoint in endpoints:
        try:
            system_info = json.loads(endpoint[5])
            rows += f'''
                <tr>
                    <td>{endpoint[1]}</td>
                    <td>{endpoint[2]}</td>
                    <td style="color: {'green' if endpoint[4] == 'online' else 'red'}">{endpoint[4]}</td>
                    <td>{endpoint[3]}</td>
                    <td>
                        <pre>{json.dumps(system_info, indent=2)}</pre>
                    </td>
                    <td>
                        <form action="/deactivate/{endpoint[0]}" method="post" style="display:inline;">
                            <button type="submit" style="color: red;">Remove</button>
                        </form>
                    </td>
                </tr>'''
        except Exception as e:
            rows += f'<tr><td colspan="6">Error processing endpoint: {str(e)}</td></tr>'

    return f'''
    <!DOCTYPE html>
    <html>
        <head>
            <title>RMM Dashboard</title>
            <meta http-equiv="refresh" content="5">
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .debug {{ background: #f0f0f0; padding: 10px; margin-bottom: 20px; }}
                pre {{ white-space: pre-wrap; margin: 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                button {{ padding: 5px 10px; border: none; cursor: pointer; }}
                button:hover {{ opacity: 0.8; }}
            </style>
        </head>
        <body>
            {debug_info}
            <h1>Endpoint Status Dashboard ({len(endpoints)} endpoints)</h1>
            <table>
                <tr>
                    <th>Hostname</th>
                    <th>IP</th>
                    <th>Status</th>
                    <th>Last Seen</th>
                    <th>System Info</th>
                    <th>Actions</th>
                </tr>
                {rows}
            </table>
        </body>
    </html>
    '''


@app.route('/deactivate/<endpoint_id>', methods=['POST'])
def deactivate(endpoint_id):
    endpoint_manager.deactivate_endpoint(endpoint_id)
    return "Endpoint deactivated successfully", 200



if __name__ == '__main__':
    comm_server = CommunicationServer()
    server_thread = threading.Thread(target=comm_server.start)
    server_thread.daemon = True
    server_thread.start()
    
    print("Starting web server on http://localhost:8080")
    app.run(host='0.0.0.0', port=8080, debug=False)