from config import settings

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

# create flask app
app = Flask(__name__)
app.config.from_object(settings)

# initialize extensions
bcrypt = Bcrypt(app)
jwt = JWTManager(app)
cors = CORS(app)
db = SQLAlchemy(app)

# register blueprints
from app.routes import server_status_routes
from app.routes import auth_routes
from app.routes import geographical_info_routes
from app.routes import land_info_routes

from app.routes import get_land_list_routes, user_land_routes

app.register_blueprint(server_status_routes)
app.register_blueprint(auth_routes)
app.register_blueprint(geographical_info_routes)
app.register_blueprint(land_info_routes)

#app.register_blueprint(user_land_routes)
#app.register_blueprint(get_land_data_routes)
#app.register_blueprint(get_land_list_routes)
