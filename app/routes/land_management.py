"""=========================================================================================
<land_management.py>

이 모듈은 사용자가 토지에 좋아요를 누르거나 토지 매물을 등록하는 것과 관련된 API 엔드포인트를 관리합니다.
주소에 대한 좌표를 검색하며, 토지 지오메트리 데이터를 검색하는 기능을 포함합니다.

주요 기능:
- PNU 코드 검색: 주어진 좌표에 대한 PNU 코드를 검색합니다.
- 좌표 검색: 주어진 주소에 대한 좌표를 검색합니다.
- 토지 지오메트리 데이터 검색: 토지 지오메트리 데이터를 검색합니다.

========================================================================================="""

# import libraries
from flask import Blueprint, request, jsonify
import flask_jwt_extended
from app import db
from app.functions.get_land_data import get_land_data
from app.functions.pnu_geolocation_lookup import get_pnu, get_word, region_code2name
from app.functions.api import GetGeometryDataAPI
from app.models.user import Users
from app.models.land import LandProperty
from app.utils.decorators import *
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))


land_management_routes = Blueprint("land_management", __name__)

@land_management_routes.route("/user_land_like", methods=["POST"])
@validation_request("email")
def user_land_like():
    """
    """
    # Error: Data format is not JSON
    if not request.is_json:
        return jsonify({
            "result":"error", 
            "msg":"missing json in request",
            "err_code":"10"
        }), 400
    
    # Error: Required parameter is empty or missing
    required_fields = ["email"]
    for field in required_fields:
        if field not in request.json or not request.json[field]:
            return jsonify({
                "result": "error", 
                "msg": f"missing {field} parameter", 
                "err_code": "11"
            }), 400

@land_management_routes.route("/register_land_property", methods=["POST"])
@flask_jwt_extended.jwt_required()
def register_land_property():
    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400
    email = flask_jwt_extended.get_jwt_identity()

    # Query for the user using email
    user = Users.query.filter_by(email=email).first()

    # 유저의 고유번호(id) 불러오기
    q = f"""
        SELECT * FROM UserInfo WHERE email='{email}'
        """
    user_data = db.executeOne(q)

    # 해당 email이 데이터베이스에 존재하지 않을 경우
    if user_data == None:
        return jsonify({"result":"error", "msg":"email does not exist"}), 401
    
    user_id = user_data["user_id"]

    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(float(lat), float(lng))

    # 매물 등록 여부 확인
    q = f"""
        SELECT * FROM land_for_sale WHERE pnu='{pnu}'
        """
    land_data = db.executeOne(q)

    # land_for_sale DB에 해당 토지의 매물 데이터가 없을 경우
    if land_data == None:
        land_area = request.json.get("land_area")
        land_price = request.json.get("land_price")
        land_summary = request.json.get("land_summary")

        q = """
            INSERT INTO land_for_sale (pnu, user_id, lat, lng, land_area, land_price, land_summary) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
        db.execute(q, (pnu, user_id, lat, lng, land_area, land_price, land_summary))
        db.commit()
        return jsonify({"result":"success", "msg":"register"}), 200
    # 이미 land_like DB에 해당 유저의 좋아요 데이터가 있을 경우 (좋아요 해제)
    else:
        if land_data["user_id"] == user_id:
            q = """
                DELETE FROM land_owner WHERE user_id='{}' AND pnu='{}'
                """.format(user_id, pnu)
            db.execute(q)
            db.commit()
            return jsonify({"result":"success", "msg":"deregister"}), 200
        else:
            return jsonify({"result":"error", "msg":"already register"}), 422