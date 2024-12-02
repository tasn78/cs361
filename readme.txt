Generate SSL certificates and private key using openssl
Install OpenSSL
Open your terminal or command prompt and run - openssl req -newkey rsa:2048 -nodes -keyout server.key -x509 -days 365 -out server.crt
server.key: The private key for the server.
server.crt: The public certificate for the server.
Follow the prompts to enter information like country, state, and organization. These can be left blank for testing purposes.
Store the server.key and server.crt files securely. For this project, place them in the same directory as your code.

This will generate the server.key (private key) and server.crt (certificate)
-server.crt will need to be copied to each client

Other option:  Generate unique certificated for each client
-openssl req -newkey rsa:2048 -nodes -keyout client1.key -x509 -days 365 -out client1.crt
-class CommunicationServer:
    def start(self):
        # Load SSL context
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile='server.crt', keyfile='server.key')
        context.load_verify_locations(cafile='ca.crt')  # Root CA or list of trusted client certs
        context.verify_mode = ssl.CERT_REQUIRED  # Enforce client certificate verification

        # Wrap the server socket
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server = context.wrap_socket(server, server_side=True)
        server.bind((self.host, self.port))
        server.listen()
        print(f"Secure server listening on {self.host}:{self.port}")

-ca.crt is the Certificate Authority file used to verify client certificates.
Each client will need to send its certificate during the handshake:
context = ssl.create_default_context()
context.load_cert_chain(certfile='client1.crt', keyfile='client1.key')  # Client-specific files

Authentication
API Key:
SHARED_SECRET = "my_secure_api_key_123"