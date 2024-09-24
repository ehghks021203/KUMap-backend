"""=========================================================================================
<land_info.py> (수정해야함)

이 모듈은 지리 정보와 관련된 API 엔드포인트를 관리합니다. 특정 좌표에 대한 PNU 코드를 검색하고, 
주소에 대한 좌표를 검색하며, 토지 지오메트리 데이터를 검색하는 기능을 포함합니다.

주요 기능:
- PNU 코드 검색: 주어진 좌표에 대한 PNU 코드를 검색합니다.
- 좌표 검색: 주어진 주소에 대한 좌표를 검색합니다.
- 토지 지오메트리 데이터 검색: 토지 지오메트리 데이터를 검색합니다.

========================================================================================="""

# import libraries
from flask import Blueprint, request, jsonify
from app.utils.decorators import *
from app.utils.exceptions import *
from app.functions import pnu_geolocation_lookup
from app.functions.get_land_data import get_land_data, set_land_predict_price_data, get_land_report_data
from app.functions.api import GetGeometryDataAPI
from app.functions.get_bid_data import get_bid_land_list_data, get_bid_case_data
from config.default import BASE_DIR

land_info_routes = Blueprint("land_info", __name__)

@land_info_routes.route("/get_land_info", methods=["GET"])
@error_handler()
def get_land_info():
    """Retrieve land information based on latitude and longitude.

    Params:
        pnu `str`:
            land code
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
    if "pnu" in request.args:
        pnu = request.args.get("pnu")
        data = get_land_data(pnu)
    elif "lat" in request.args and "lng" in request.args:
        lat = request.args.get("lat")
        lng = request.args.get("lng")
        pnu, _ = pnu_geolocation_lookup.get_pnu(lat, lng)
        data = get_land_data(pnu)
    else:
        raise MissingParamException()
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

@land_info_routes.route("/get_land_predict_price", methods=["GET"])
def get_land_predict_price():
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
    validate_args_params("pnu")
    pnu = request.args.get("pnu")
    set_land_predict_price_data(pnu)
    data = get_land_data(pnu)
    
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

@land_info_routes.route("/get_bid", methods=["GET"])
def get_bid():
    """특정 토지의 경매 데이터 조회

    Params:
        pnu `str`: 
            토지의 PNU 코드(19자리)
    
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        err_code `str`:
            오류 코드 (API_GUIDE.md 참고)
        data `list`:
            법원 경매 데이터를 담은 리스트
    """
    pnu = request.args.get("pnu")
    if not pnu:
        return jsonify({
            "result":"error", 
            "msg":"pnu parameter missing",
            "err_code":"11"    
        }), 400

    data = get_bid_land_list_data(pnu[0:2], pnu[2:5])
    if data != None:
        for d in data:
            print(data)
    else:
        return jsonify({
            "result":"error", 
            "msg":"bid data for the requested PNU code does not exist",
            "err_code":"30"
        }), 422

        

    #q = """
    #    SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'
    #    """.format(sql_res["case_cd"], sql_res["obj_nm"], sql_res["court_in_charge"])
    #case_info = db.executeOne(q)
    #sql_res["case_info"] = case_info
    #sql_res["case_info"]["date_list"] = json.loads(sql_res["case_info"]["date_list"])
    #sql_res["case_info"]["land_list"] = json.loads(sql_res["case_info"]["land_list"])
    return jsonify({
        "result":"success", 
        "msg":"get bid data", 
        "err_code":"00",
        "data":data
    }), 200

@land_info_routes.route("/get_land_report", methods=["POST"])
@error_handler()
def get_land_report():
    validate_json_params("pnu")
    pnu = request.json.get("pnu")

    data = get_land_report_data(pnu)
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
            "report":data
        }), 200

