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
from app.functions import pnu_geolocation_lookup
from app.functions.api import GetGeometryDataAPI
from config import api
from config.default import BASE_DIR

geographical_info_routes = Blueprint("geographical_info", __name__)

# END (2024.05.20.)
@geographical_info_routes.route("/get_pnu", methods=["GET"])
def get_pnu():
    """Retrieve the PNU code for the given coordinates.
        
    Params:
        lat `float`: 
            Latitude coordinate
        lng `float`: 
            Longitude coordinate

    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        pnu `str`:
            19-digit PNU code
        addressName `str`:
            Land parcel address
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
    
    # Retrieve PNU code and address
    pnu, address = pnu_geolocation_lookup.get_pnu(float(lat), float(lng))
    if pnu == None or address == None:
        return jsonify({
            "result":"error", 
            "msg":"PNU code for the requested coordinates does not exist",
            "err_code":"30"
        }), 422
    else:
        return jsonify({
            "result":"success", 
            "msg":"get pnu", 
            "err_code":"00",
            "pnu":pnu, 
            "addressName":address
        }), 200

# END (2024.05.20.)
@geographical_info_routes.route("/get_coord", methods=["GET"])
def get_word():
    """Retrieve the coordinates for the given address.

    Params:
        word `str`: 
            Land parcel address
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        lat `float`:
            Latitude coordinate
        lng `float`:
            Longitude coordinate
        address `str`:
            Land parcel address
    """
    word = request.args.get("word")

    # Error: Parameter is missing
    if not word:
        return jsonify({
            "result":"error", 
            "msg":"missing word parameter", 
            "err_code":"11"
        }), 400
    
    # Retrieve coordinates for the given address
    lat, lng = pnu_geolocation_lookup.get_word(word)
    if lat == None or lng == None:
        return jsonify({
            "result":"error", 
            "msg":"address does not exist",
            "err_code":"30"
        }), 422
    else:
        return jsonify({
            "result":"success", 
            "msg":"get address lat lng", 
            "err_code":"00",
            "lat":lat, 
            "lng":lng
        }), 200

# END (2024.05.20.)
@geographical_info_routes.route("/get_land_geometry", methods=["GET"])
def get_geo():
    """Retrieve land geometry data.

    Type: 2D Data API 2.0
    Category: Land
    Service Name: Cadastral Map
    Service ID: LP_PA_CBND_BUBUN
    Provider: Ministry of Land, Infrastructure and Transport

    Params:
        lat `float`: 
            Latitude coordinate
        lng `float`: 
            Longitude coordinate
        pnu `str`:
            Parcel number (optional)
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        geometry `list`:
            Land geometry data
    """    
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    pnu = request.args.get("pnu")
    
    if pnu:
        if lat or lng:
            return jsonify({
                "result":"error", 
                "msg":"you cannot request pnu and coordinates at the same time", 
                "err_code":"11"
            }), 400
    else:
        if not lat or not lng:
            return jsonify({
                "result":"error", 
                "msg":"request parameter missing", 
                "err_code":"11"
            }), 400
        else:
            pnu, address = pnu_geolocation_lookup.get_pnu(float(lat), float(lng))

    geo_api = GetGeometryDataAPI(key=api.VWORLD_API_KEY)
    res = geo_api.get_data(pnu=pnu)
    if not res:
        return jsonify({
            "result":"error", 
            "msg":"geometry data for the requested coordinates does not exist",
            "err_code":"30"
        }), 422
    # Generate GeoJSON
    return jsonify({
        "result":"success", 
        "msg":"get land geometry data", 
        "err_code":"00",
        "geometry":res["features"][0]["geometry"]["coordinates"]
    }), 200

@geographical_info_routes.route("/load_addr_csv", methods=["GET"])
def load_addr_csv():
    """Load address data from a CSV file.

    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        data `dict`:
            Address data loaded from the CSV file
    """
    f = open(BASE_DIR + "/data/PnuCode.csv", "r", encoding="utf-8")
    lines = f.readlines()
    data = {}
    for line in lines:
        if line.split(",")[1] == "sido":
            continue
        if line.split(",")[1] not in data:
            data[line.split(",")[1]] = {}
        else:
            if line.split(",")[2] != "" and line.split(",")[2] not in data[line.split(",")[1]]:
                data[line.split(",")[1]][line.split(",")[2]] = []
            else:
                if line.split(",")[3] != "" and line.split(",")[3] not in data[line.split(",")[1]][line.split(",")[2]]:
                    data[line.split(",")[1]][line.split(",")[2]].append(line.split(",")[3])
    f.close()
    return jsonify({
        "result":"success", 
        "msg":"load address csv data", 
        "err_code":"00",
        "data":data
    }), 200

@geographical_info_routes.route("/get_all_geo_data", methods=["GET"])
def get_all_geo(lat, lng, level, target_filter="all"):
    # TODO: 나중에 하자.. 나중에..
    return jsonify({
        "result":"success", 
        "msg":"", 
        "err_code":"00"
    }), 200
