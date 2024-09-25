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
from app.models.user import Users, UserLandLike
from app.models.land import LandProperty
from app.utils.decorators import *
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))


land_management_routes = Blueprint("land_management", __name__)

@land_management_routes.route("/land_like", methods=["POST"])
def LandLike():
    '''
    토지 좋아요
        Params:
            email `str`
    '''

    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400

    email = request.json.get("email")
    pnu = request.json.get("pnu")

    # Query for the user using email
    user = Users.query.filter_by(email=email).first()
    # If user does not exist
    if user is None:
        return jsonify({"result": "error", "msg": "email does not exist"}), 401
    # Get the user's ID
    user_id = user.user_id
    # Check if the land is already liked by the user
    existing_like = UserLandLike.query.filter_by(user_id=user_id, pnu=pnu).first()
    if existing_like:
        # If a like record exists, delete it (unlike)
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({"result": "success", "msg": "unlike"}), 200
    else:
        # If no like record exists, add a new like
        new_like = UserLandLike(user_id=user_id, pnu=pnu)
        db.session.add(new_like)
        db.session.commit()
        return jsonify({"result": "success", "msg": "like"}), 200

@land_management_routes.route("/register_land_property", methods=["POST"])
@flask_jwt_extended.jwt_required()
def register_land_property():
    if not request.is_json:
        return jsonify({'result': 'error', 'msg': 'missing json in request'}), 400

    email = flask_jwt_extended.get_jwt_identity()
    user = Users.query.filter_by(email=email).first()

    if user is None:
        return jsonify({"result": "error", "msg": "email does not exist"}), 401
    
    user_id = user.user_id

    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(lat, lng)

    land_data = LandProperty.query.filter_by(pnu=pnu).first()

    if land_data is None:
        land_area = request.json.get("land_area")
        land_price = request.json.get("land_price")
        land_summary = request.json.get("land_summary")

        new_land_property = LandProperty(
            pnu=pnu,
            user_id=user_id,
            lat=lat,
            lng=lng,
            area=land_area,
            price=land_price,
            summary=land_summary,
        )
        db.session.add(new_land_property)
        db.session.commit()
        return jsonify({"result": "success", "msg": "register"}), 200
    else:
        if land_data.user_id == user_id:
            db.session.delete(land_data)
            db.session.commit()
            return jsonify({"result": "success", "msg": "deregister"}), 200
        else:
            return jsonify({"result": "error", "msg": "already registered"}), 422
        