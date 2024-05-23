from config.default import *
import os

# Server Configurations
SERVER_DOMAIN = os.getenv("SERVER_DOMAIN", "localhost")
SERVER_PORT = os.getenv("SERVER_PORT", 5000)
SERVER_PASSWORD = os.getenv("SERVER_PASSWORD", "default_server_password")
SSL_CERTIFICATE_PATH = os.getenv("SSL_CERTIFICATE_PATH", None)
SSL_KEY_PATH = os.getenv("SSL_KEY_PATH", None)
