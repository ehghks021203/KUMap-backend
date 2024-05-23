from app import app

from .server_status import server_status_routes

from .auth import auth_routes
from .geographical_info import geographical_info_routes
from .land_info import land_info_routes

#from .get_land_data import get_land_data_routes
from .get_land_list import get_land_list_routes
from .user_land import user_land_routes
