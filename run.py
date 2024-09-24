import ssl
from app import app
from config import server

if __name__ == "__main__":
    SSL_CONTEXT = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    SSL_CONTEXT.load_cert_chain(
        certfile=server.SSL_CERTIFICATE_PATH, 
        keyfile=server.SSL_KEY_PATH, 
        password=server.SERVER_PASSWORD
    )
    app.run(host=server.SERVER_DOMAIN, port=server.SERVER_PORT, ssl_context=SSL_CONTEXT, debug=True)
