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
from app import db
from app.functions.get_land_data import get_land_data
from app.functions.pnu_geolocation_lookup import get_pnu, get_word, region_code2name
from app.functions.api import GetGeometryDataAPI
from app.functions.convert_code import code2addr_dict
from app.functions.get_bid_data import get_bid_land_list_data, get_bid_case_data
from app.models.user import Users
from app.models.land import LandProperty
import os
import sys
import json
from datetime import datetime
import pytz
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

land_list_routes = Blueprint("land_list", __name__)

@land_list_routes.route("/get_auction_list", methods=["GET"])
def get_auction_list():
    """경매 목록 조회 함수
    
    Params:
        lat `float`: 
            위도 좌표
        lng `float`: 
            경도 좌표
        zoom `int`:
            맵의 줌 레벨 (1: 시/도, 2: 시/군/구)

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
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    zoom = request.args.get("zoom")

    # Error: 법원경매 홈페이지 점검
    if 1 <= datetime.now(pytz.timezone('Asia/Seoul')).time().hour < 6:
        return jsonify({
            "result":"error", 
            "msg":"bid api service under maintenance",
            "err_code":"51",
            "data": []
        }), 200

    # Error: 파라미터 값이 비어있거나 없음
    if not lat or not lng:
        return jsonify({
            "result":"error", 
            "msg":"missing lat or lng parameter",
            "err_code":"11"
        }), 400
    if not zoom:
        zoom = 2
    pnu, address = get_pnu(float(lat), float(lng))
    if pnu == None or address == None:
        return jsonify({
            "result":"error", 
            "msg":"land bid list for the requested coordinates does not exist",
            "err_code":"30"
        }), 422
    
    if zoom == 1:
        data = get_bid_land_list_data(pnu[0:2])
    else:
        data = get_bid_land_list_data(pnu[0:2], pnu[2:5])
    for i in range(len(data)):
        lat, lng = get_word(data[i]["addr"]["address"])
        case_info = get_bid_case_data(data[i]["court_in_charge"], data[i]["case_cd"], data[i]["obj_nm"])
        data[i]["lat"] = lat
        data[i]["lng"] = lng
        data[i]["case_info"] = case_info
        data[i]["case_info"]["date_list"] = json.loads(data[i]["case_info"]["date_list"])
        data[i]["case_info"]["land_list"] = json.loads(data[i]["case_info"]["land_list"])
    
    return jsonify({
        "result":"success", 
        "msg":"get bid list",
        "err_code":"00",
        "data": data
    }), 200


@land_list_routes.route("/get_land_property_list", methods=["GET"])
def get_land_property_list():
    """경매 목록 조회

    Params:
        lat `float`: 
            위도 좌표
        lng `float`: 
            경도 좌표
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        data `list`:
            토지 매물 데이터를 담은 리스트
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    # Error: 파라미터 값이 비어있거나 없음
    if not lat or not lng:
        return jsonify({
            "result": "error", 
            "msg": "lat or lng parameter missing",
            "err_code": "11"
        }), 400

    pnu, address = get_pnu(float(lat), float(lng))
    pnu = pnu[0:5]

    land_property_list = db.session.query(
        Users.name,
        Users.nickname,
        LandProperty.pnu,
        LandProperty.lat,
        LandProperty.lng,
        LandProperty.area,
        LandProperty.price,
        LandProperty.summary,
        LandProperty.reg_date
    ).join(LandProperty, Users.user_id == LandProperty.user_id)\
     .filter(LandProperty.pnu.like(f"{pnu}%"))\
     .all()

    # 결과를 딕셔너리로 변환
    land_property_list = [
        {
            "name": l[0],
            "nickname": l[1],
            "pnu": l[2],
            "address": code2addr_dict(l[2]),
            "lat": l[3],
            "lng": l[4],
            "land_area": l[5],
            "land_price": l[6],
            "land_summary": l[7],
            "reg_date": l[8].strftime("%Y.%m.%d %H:%M")  # 날짜 형식 변환
        }
        for l in land_property_list
    ]

    # 각 토지 데이터에 추가 정보 추가
    for l in land_property_list:
        land_response = get_land_data(l["pnu"])
        l["land_info"] = land_response
    
    return jsonify({
        "result": "success",  # 성공 응답으로 변경
        "msg": "get land sale list", 
        "err_code": "00",
        "data": land_property_list
    }), 200


