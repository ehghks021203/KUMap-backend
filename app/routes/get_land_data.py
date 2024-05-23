from config import BASE_DIR, Database, Key
from app.functions.pnu_geolocation_lookup import get_pnu, get_word
from app.functions.get_land_data import get_land_data

from flask import Blueprint, request, jsonify
import json
import requests

get_land_data_routes = Blueprint("get_land_data", __name__)

@get_land_data_routes.route("/get_land_info", methods=["GET"])
def GetLandInfo():
    """위경도 값으로 토지 정보 받아오기.

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
        err_code `str`:
            오류 코드 (API_GUIDE.md 참고)
        data `dict`: 토지 특성 정보를 딕셔너리 형태로 반환.
            pnu `str`:
                토지의 19자리 주소 코드
            addr `str`:
                토지의 지번 주소
            official_land_price `int`:
                토지의 공시지가 (현재 기준년도: 2022년도)
            predict_land_price `int`:
                토지의 예측 실거래가
            land_classification `str`:
                토지의 지목
            land_zoning `str`:
                토지의 용도지역
            land_use_situation `str`:
                토지의 이용상황
            land_register `str`:
                토지의 필지 (일반 혹은 산)
            land_area `str`:
                토지의 면적 (제곱미터)
            land_height `str`:
                토지의 지세
            land_form `str`:
                토지의 형상
            road_side `str`:
                토지의 도로접면
            land_uses `str`:
                토지의 이용 계획(구분자: '/')
            real_price_data `list`:
                토지 주변 지역의 실거래 내역 
            bid_data `dict`:
                토지의 경매 정보 (없다면 null)
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")

    # Error: 파라미터 값이 비어있거나 없음
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

@get_land_data_routes.route("/get_bid", methods=["GET"])
def GetBid():
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

    db = Database()

    q = """
        SELECT * FROM Bid_LandList WHERE pnu='{}'
        """.format(pnu)
    sql_res = db.executeOne(q)

    if sql_res == None:
        return jsonify({
            "result":"error", 
            "msg":"bid data for the requested PNU code does not exist",
            "err_code":"30"
        }), 422

    q = """
        SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'
        """.format(sql_res["case_cd"], sql_res["obj_nm"], sql_res["court_in_charge"])
    case_info = db.executeOne(q)
    sql_res["case_info"] = case_info
    sql_res["case_info"]["date_list"] = json.loads(sql_res["case_info"]["date_list"])
    sql_res["case_info"]["land_list"] = json.loads(sql_res["case_info"]["land_list"])
    return jsonify({
        "result":"success", 
        "msg":"get bid data", 
        "err_code":"00",
        "data":sql_res
    }), 200

