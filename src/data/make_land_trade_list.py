import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from app.functions.api import LandTradeAPI
from config import api

if __name__ == "__main__":
    api = LandTradeAPI(key=api.LAND_TRADE_API_KEY)
    response = api.get_data("11110", 2010, 1)
    print(response)

