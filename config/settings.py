from config.default import *
import os
from datetime import timedelta

# General Flask Configurations
JSON_AS_ASCII = os.getenv("JSON_AS_ASCII", False)
SECRET_KEY = os.getenv("SECRET_KEY", "default_secret_key")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt_secret_key")
JWT_ACCESS_TOKEN_EXPIRES = timedelta(int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 360)))
JWT_REFRESH_TOKEN_EXPIRES = timedelta(int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", 720)))

MAIL_SERVER = os.getenv("MAIL_SERVER", "smtp.gmail.com")
MAIL_PORT = os.getenv("MAIL_PORT", 465)
MAIL_USERNAME = os.getenv("MAIL_USERNAME", "default_username")
MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "default_password")
MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", False)
MAIL_USE_SSL = os.getenv("MAIL_USE_SSL", True)

SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI", "sqlite:///default.db")
SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", False)