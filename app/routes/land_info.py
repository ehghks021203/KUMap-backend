"""=========================================================================================
<geographical_info.py>

이 모듈은 지리 정보와 관련된 API 엔드포인트를 관리합니다. 특정 좌표에 대한 PNU 코드를 검색하고, 
주소에 대한 좌표를 검색하며, 토지 지오메트리 데이터를 검색하는 기능을 포함합니다.

주요 기능:
- PNU 코드 검색: 주어진 좌표에 대한 PNU 코드를 검색합니다.
- 좌표 검색: 주어진 주소에 대한 좌표를 검색합니다.
- 토지 지오메트리 데이터 검색: 토지 지오메트리 데이터를 검색합니다.

========================================================================================="""

# import libraries
from flask import Blueprint, request, jsonify
from app.functions.get_land_data import get_land_data
from app.functions.api import GetGeometryDataAPI
from config.default import BASE_DIR

land_info_routes = Blueprint("land_info", __name__)

@land_info_routes.route("/get_land_info", methods=["GET"])
def get_land_info():
    """Retrieve land information based on latitude and longitude.

    Params:
        lat `float`:
            Latitude coordinate
        lng `float`:
            Longitude coordinate
    Returns:
        result `str`:
            Response success or error status ("success" or "error")
        msg `str`:
            Response message
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        data `dict`: 
            Land attribute information returned in dictionary format.
            - pnu `str`:
                19-digit address code of the land
            - addr `str`:
                Parcel address of the land
            - official_land_price `int`:
                Official land price of the land (current base year: 2022)
            - predict_land_price `int`:
                Predicted transaction price of the land
            - land_classification `str`:
                Classification of the land
            - land_zoning `str`:
                Zoning of the land
            - land_use_situation `str`:
                Land use situation
            - land_register `str`:
                Registration of the land (general or mountainous)
            - land_area `str`:
                Area of the land (square meters)
            - land_height `str`:
                Elevation of the land
            - land_form `str`:
                Form of the land
            - road_side `str`:
                Roadside of the land
            - land_uses `str`:
                Land use plans (separated by '/')
            - real_price_data `list`:
                Real transaction records of nearby areas
            - bid_data `dict`:
                Auction information of the land (if available, otherwise null)
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    # Error: Parameters are missing
    if not lat or not lng:
        return jsonify({
            "result":"error", 
            "msg":"missing lat or lng parameter", 
            "err_code":"11"
        }), 400
    
    data = get_land_data(float(lat), float(lng))
    if data == None:
        return jsonify({
            "result":"error", 
            "msg":"land information for the requested coordinates does not exist",
            "err_code":"30",
        }), 422
    else:
        return jsonify({
            "result":"success", 
            "msg":"get land information", 
            "err_code":"00",
            "data":data
        }), 200
    
#def get_bid()
    
#def get_bid_list()
    
#def get_sale_list()
    
