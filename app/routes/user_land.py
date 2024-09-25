"""=========================================================================================
<user_land.py> * 수정해야함

이 모듈은 사용자 인증과 관련된 API 엔드포인트를 관리합니다. 로그인, 회원가입, 이메일 및 닉네임 중복 
확인, 사용자 인증 확인과 같은 기능을 제공합니다.

주요 기능:
- 사용자 로그인: 이메일과 비밀번호를 사용하여 사용자를 인증하고 JWT 토큰을 발급합니다.
- 사용자 회원가입: 사용자의 이름, 닉네임, 이메일, 비밀번호를 등록합니다.
- 이메일/닉네임 중복 확인: 새 사용자 등록 시 이메일 또는 닉네임이 이미 사용 중인지 확인합니다.
- 사용자 인증 확인: 요청을 보낸 사용자의 JWT 토큰을 확인하여 인증 상태를 검증합니다.

이 모듈은 Flask와 SQLAlchemy를 사용하여 구현되었으며, JWT를 사용하여 사용자 인증을 처리합니다.

========================================================================================="""

# import libraries
# import app
from app import db
from app.functions.pnu_geolocation_lookup import get_pnu, get_word
from app.functions.get_land_data import get_land_data
from app.utils.exceptions import *
from app.utils.decorators import *
from app.models.user import Users, UserLandLike


from flask import Blueprint, request, jsonify
import flask_jwt_extended
import json
import requests

user_land_routes = Blueprint("user_land", __name__)

@user_land_routes.route("/load_land_like", methods=["POST"])
def LoadLandLike():
    '''
    토지의 좋아요 개수 및 유저의 토지 좋아요 여부를 확인하는 함수.
        Params:
            email `str`
    '''

    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400

    
    email = request.json.get("email")
    db = Database()

    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(lng, lat)

    # 좋아요 목록 불러오기
    q = """
        SELECT * FROM land_like WHERE pnu='{}'
        """.format(pnu)
    likeData = db.executeAll(q)

    totalLikeCount = len(likeData)
    isLike = False
    
    # 유저의 고유번호(id) 불러오기
    q = """
        SELECT * FROM UserInfo WHERE email='{}'
        """.format(email)
    userData = db.executeAll(q)
    

    if len(userData) != 0:
        userId = userData[0]["user_id"]
        for i in range(totalLikeCount):
            if (likeData[i]["user_id"] == userId):
                isLike = True
    
    return jsonify(total_like=totalLikeCount, is_like=isLike), 200

@user_land_routes.route("/user_land_like_list", methods=["POST"])
@flask_jwt_extended.jwt_required()
@error_handler()
def UserLandLikeList():
    '''유저의 좋아요 목록 불러오기
        Params:
            email `str`: 유저의 이메일
        Returns:
            `list`: 딕셔너리 리스트 형태로 반환
    '''
    curr_user_email = flask_jwt_extended.get_jwt_identity()

    user = Users.query.filter_by(email=curr_user_email).first()
    # If user not exist
    if not user:
        return jsonify({
            "result": "error",
            "msg": "user does not exist",
            "err_code": "20"
        }), 422
    
    user_land_like_list = UserLandLike.query.filter_by(user_id=user.user_id).all()

    user_land_like_data = []
    
    for land in user_land_like_list:
        land_response = get_land_data(land.pnu)
        user_land_like_data.append(land_response)

    return jsonify(user_land_like_data=user_land_like_data), 200


@user_land_routes.route("/reg_land_for_sale", methods=["POST"])
@flask_jwt_extended.jwt_required()
def RegLandForSale():
    '''
    토지 매물 등록
        Params:
            email `str`
    '''
    print(request.get_json())

    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400
    email = flask_jwt_extended.get_jwt_identity()

    # DB 연결
    db = Database()

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

@user_land_routes.route("/dereg_land_for_sale", methods=["POST"])
def DeregLandForSale():
    '''
    토지 매물 등록 해지
        Params:
            email `str`
    '''

    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400

    email = request.json.get("email")
    db = Database()

    # 유저의 고유번호(id) 불러오기
    q = """
        SELECT * FROM UserInfo WHERE email='{}'
        """.format(email)
    userData = db.executeAll(q)

    # 해당 email이 데이터베이스에 존재하지 않을 경우
    if len(userData) == 0:
        return jsonify({"result":"error", "msg":"email does not exist"}), 401
    
    userId = userData[0]["user_id"]


    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(lng, lat)

    # 매물 등록 여부 확인
    q = """
        SELECT * FROM land_for_sale WHERE pnu='{}'
        """.format(pnu)
    landData = db.executeAll(q)


    # land_for_sale DB에 해당 토지의 매물 데이터가 없을 경우
    if len(landData) != 0:
        q = """
            DELETE FROM land_for_sale WHERE user_id='{}' AND pnu='{}'
            """.format(userId, pnu)
        db.execute(q)
        db.commit()
        return jsonify({"result":"success", "msg":"deregister"}), 200

@user_land_routes.route("/user_land_for_sale_list", methods=["POST"])
def UserLandForSaleList():
    '''유저의 좋아요 목록 불러오기
        Params:
            email `str`: 유저의 이메일
        Returns:
            `list`: 딕셔너리 리스트 형태로 반환
    '''

    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({'result':'error', 'msg':'missing json in request'}), 400

    
    email = request.json.get("email")
    db = Database()

    # 유저의 고유번호(id) 불러오기
    q = """
        SELECT * FROM UserInfo WHERE email='{}'
        """.format(email)
    userData = db.executeAll(q)

    # 해당 이메일로 유저가 조회되지 않을 경우
    if len(userData) == 0:
        return jsonify({'result':'error', 'msg':'user dose not found'}), 401
    
    userId = userData[0]["user_id"]
        
    # 좋아요 목록 불러오기
    q = "SELECT * FROM land_for_sale WHERE user_id={}".format(userId)
    sql_res = db.executeAll(q)

    for i in range(len(sql_res)):
        land_response = get_land_data(float(sql_res[i]["lat"]), float(sql_res[i]["lng"]))
        sql_res[i]["land_info"] = land_response
        sql_res[i]["reg_date"] = sql_res[i]["reg_date"].strftime("%Y.%m.%d %H:%M")
    
    return jsonify(land_for_sale=sql_res), 200