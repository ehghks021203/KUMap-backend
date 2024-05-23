from flask import Flask
from flask import jsonify, request
import flask_jwt_extended
from flask_mysqldb import MySQL
from flask_cors import CORS
from flask_mail import Mail, Message

from PyKakao import Local

import json
import requests
import ssl
import bcrypt
import string
import random

WORKSPACE = "/home/students/cs/202120990/server/"

app = Flask(__name__)
cors = CORS(app)
mail = Mail(app)

# JSON 데이터를 ASCII 인코딩이 아닌 UTF-8 방식으로 인코딩하도록 설정
app.config["JSON_AS_ASCII"] = False

# Flask MySQL 구성
app.config["MYSQL_USER"] = "landprice"
app.config["MYSQL_PASSWORD"] = "landprice123"
app.config["MYSQL_DB"] = "landprice_db"
app.config["MYSQL_HOST"] = "localhost"
app.config["MYSQL_PORT"] = 3306
app.config["MYSQL_CURSORCLASS"] = "DictCursor"

mysql = MySQL(app)

# Flask JWT extension 설정
app.config["JWT_SECRET_KEY"] = "landpricejwtsecretkey8403598*"
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = 360
app.config["JWT_REFRESH_TOKEN_EXPIRES"] = 720

jwt = flask_jwt_extended.JWTManager(app)

# Flask Mail 구성
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USERNAME"] = "landpricekku@gmail.com"
app.config["MAIL_PASSWORD"] = "ghgimxxgnrtwmusm"
app.config["MAIL_USE_TLS"] = False
app.config["MAIL_USE_SSL"] = True

def region_code2name(code: str) -> str:
    """
    두 자리 수의 시도 코드를 시도 명으로 변환해주는 코드.
    ex) region_code2name('11') --> 'Seoul'
    """
    code2name = {
        '11':'Seoul', 
        '26':'Busan', 
        '27':'Daegu', 
        '28':'Incheon', 
        '29':'Gwangju', 
        '30':'Daejeon', 
        '31':'Ulsan', 
        '36':'Sejong',
        '41':'Gyeonggido', 
        '42':'Gangwondo', 
        '43':'Chungcheongbukdo', 
        '44':'Chungcheongnamdo', 
        '45':'Jeollabukdo', 
        '46':'Jeollanamdo', 
        '47':'Gyeongsangbukdo', 
        '48':'Gyeongsangnamdo', 
        '50':'Jejudo'    
    }
    return code2name[code]

def get_pnu(lat: float, lng: float):
    """입력된 좌표의 PNU 코드 조회
        
    Params:
        lat `float`: 
            위도 좌표
        lng `float`: 
            경도 좌표
    Returns:
        pnu `str`:
            19자리 PNU 코드
        addressName `str`:
            토지 지번 주소
    """
    # 로컬 API 인스턴스 생성
    local = Local(service_key = "97d8aaa759dde2a7c32d51778c9ad2f2")
    request_address = local.geo_coord2address(lng, lat, dataframe=False)
    request_region = local.geo_coord2regioncode(lng, lat, dataframe=False)
    if request_region == None:
        return None, None
    i = 0 if request_region["documents"][0]["region_type"] == "B" else 1
    pnu = request_region["documents"][i]["code"]
    address_name = request_region["documents"][i]["address_name"]
    
    if request_address["meta"]["total_count"] == 0:
        return pnu, address_name
    address_name = address_name + " " + request_address["documents"][i]["address"]["main_address_no"]
    if request_address["documents"][i]["address"]["sub_address_no"] != "":
        address_name = address_name + "-" + request_address["documents"][i]["address"]["sub_address_no"]
    if request_address["documents"][i]["address"]["mountain_yn"] == "N":
        mountain = "1"   # 산 X
    else:
        mountain = "2"   # 산 O

    # 본번과 부번의 포멧을 '0000'으로 맞춰줌
    main_no = request_address["documents"][0]["address"]["main_address_no"].zfill(4)
    sub_no = request_address["documents"][0]["address"]["sub_address_no"].zfill(4)
    pnu = str(pnu + mountain + main_no + sub_no)
    return pnu, address_name

def get_word(word: str):
    """입력된 주소의 좌표 조회

    Params:
        word `str`: 
            지번 주소
    Returns:
        lat `float`:
            위도 좌표
        lng `float`:
            경도 좌표
        address `str`:
            지번 주소
    """
    # 로컬 API 인스턴스 생성
    local = Local(service_key="97d8aaa759dde2a7c32d51778c9ad2f2")
    request_address = local.search_address(word, dataframe=False)

    if len(request_address["documents"]) == 0:
        return None, None, None
    lng = request_address["documents"][0]["x"]
    lat = request_address["documents"][0]["y"]
    return lat, lng

def get_land_info(lat: float, lng: float):
    """위경도 값으로 토지 정보 받아오기.

    Params:
        lat `float`:
            위도 값
        lng `float`:
            경도 값
    Returns:
        `dict`: 토지 특성 정보를 딕셔너리 형태로 반환.
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
    pnu, address = get_pnu(lat, lng)
    if pnu == None or address == None:
        return None
    region = region_code2name(pnu[0:2])

    main_num = pnu[11:15]
    for i in range(len(main_num)):
        if main_num[i] != "0":
            if (i >=3):
                main_num = "000"
                break
            main_num = main_num[0:i+1]
            break

    cur = mysql.connect.cursor()
    sql = "SELECT * FROM {}_LandInfo WHERE pnu='{}'".format(region, pnu)
    cur.execute(sql)
    sql_res = cur.fetchone()
    if sql_res == None:
        cur.close()
        return None
    
    # 실거래 내역 조회
    sql = "SELECT * FROM {}_RealPriceInfo WHERE pnu='{}' AND land_classification='{}' AND land_zoning='{}'".format(
        region, pnu[0:11] + main_num, sql_res["land_classification"], sql_res["land_zoning"]
        )
    cur.execute(sql)
    sql_res_rd = cur.fetchall()

    # 법원 경매 데이터 조회
    sql = "SELECT * FROM Bid_LandList WHERE pnu='{}'".format(pnu)
    cur.execute(sql)
    sql_res_bd = cur.fetchone()
    if sql_res_bd != None:
        sql = " SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'".format(
            sql_res_bd["case_cd"], sql_res_bd["obj_nm"], sql_res_bd["court_in_charge"]
        )
        cur.execute(sql)
        case_info = cur.fetchone()
        sql_res_bd["case_info"] = case_info
        sql_res_bd["case_info"]["date_list"] = json.loads(sql_res_bd["case_info"]["date_list"])
        sql_res_bd["case_info"]["land_list"] = json.loads(sql_res_bd["case_info"]["land_list"])
        for i in range(len(sql_res_bd['case_info']['land_list'])):
            lat, lng = get_word(sql_res_bd['case_info']['land_list'][i]['addr'])
            sql_res_bd['case_info']['land_list'][i]['lat'] = lat
            sql_res_bd['case_info']['land_list'][i]['lng'] = lng

    # 토지 매물 데이터 조회
    sql = """
        SELECT u.name, u.nickname, u.phone, l.pnu, l.lat, l.lng, 
        l.land_area, l.land_price, l.land_summary, l.reg_date 
        FROM UserInfo u, land_for_sale l 
        WHERE u.user_id=l.user_id
        AND l.pnu='{}'
        """.format(pnu)
    cur.execute(sql)
    sql_res_sd = cur.fetchone()

    # 좋아요 목록 불러오기
    sql = "SELECT * FROM land_like WHERE pnu='{}'".format(pnu)
    cur.execute(sql)
    sql_res_like = cur.fetchall()
    total_like = len(sql_res_like)
    cur.close()
    land_dict = {
        "pnu":                  pnu,
        "addr":                 address,
        "official_land_price":  sql_res["official_land_price"],
        "predict_land_price":   sql_res["predict_land_price"],
        "land_classification":  sql_res["land_classification"],
        "land_zoning":          sql_res["land_zoning"],
        "land_use_situation":   sql_res["land_use_situation"],
        "land_register":        sql_res["land_register"],
        "land_area":            sql_res["land_area"],
        "land_height":          sql_res["land_height"],
        "land_form":            sql_res["land_form"],
        "road_side":            sql_res["road_side"],
        "land_uses":            sql_res["land_uses"],
        "real_price_data":      sql_res_rd,
        "bid_data":             sql_res_bd,
        "sale_data":            sql_res_sd,
        "total_like":           total_like,
    }
    return land_dict


@app.route("/", methods=["GET", "POST"])
def ServerStatus():
    return jsonify({"result":"success", 'msg':"server is online"}), 200

@app.route("/login", methods=["POST"])
def Login():
    """유저 로그인 함수.
    
    Params:
        email `str`:
            유저의 이메일 주소.
        password `str`:
            유저의 비밀번호.
    
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        access_token `str`:
            엑세스 토큰
        refresh_token `str`:
            리프레쉬 토큰
    """
    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({"result":"error", "msg":"missing json in request"}), 400

    # POST로 인자 값 받아오기
    email = request.json.get("email")
    password = request.json.get("password")
    if not email:
        return jsonify({"result":"error", "msg":"missing email parameter"}), 400
    if not password:
        return jsonify({"result":"error", 'msg':"missing password parameter"}), 400
    
    # DB 안의 user 테이블 접근 (입력받은 email이 DB 안에 존재하는지 확인)
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    sql_res = cur.fetchone()
    cur.close()

    # user 테이블 내에 요청받은 email 데이터가 존재하지 않음
    if (sql_res == None):
        return jsonify({"result":"error", "msg":"email does not exist"}), 422
    # user 테이블 내에 요청받은 email 데이터가 존재함
    else:
        # password가 동일한지 확인
        password = password.encode("utf-8")
        sql_res["password"] = sql_res["password"].encode("utf-8")
        # password가 다를 경우
        if (not bcrypt.checkpw(password, sql_res["password"])):
            return jsonify({"result":"error", "msg":"incorrect password"}), 401
        # password가 일치할 경우
        else:
            # 엑세스 토큰 및 리프레시 토큰 설정
            access_token = flask_jwt_extended.create_access_token(identity=email)
            refresh_token = flask_jwt_extended.create_refresh_token(identity=email)
            return jsonify({"result":"success", 'msg':"login", "access_token":access_token, "refresh_token":refresh_token}), 200

@app.route("/dup_check", methods=["POST"])
def DupCheck():
    """유저 회원가입 중복체크. email 혹은 nickname 값 둘 중 하나만 요청해도 응답

    Params:
        email `str`:
            사용자의 이메일
        nickname `str`:
            사용자의 닉네임
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
    """
    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({"result":"error", "msg":"missing json in request"}), 400

    # POST로 인자 값 받아오기
    email = request.json.get("email")
    nickname = request.json.get("nickname")
    
    if not email and not nickname:
        return jsonify({"result":"error", "msg":"missing email or nickname parameter"}), 400

    # DB 연결
    cur = mysql.connection.cursor()

    if email:
        sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
        cur.execute(sql) 
        sql_res = cur.fetchall()
        if len(sql_res) != 0:
            cur.close()
            return jsonify({"result":"error", "msg":"duplicate nickname"}), 409
    if nickname:
        sql = "SELECT * FROM UserInfo WHERE nickname='{}'".format(nickname)
        cur.execute(sql) 
        sql_res = cur.fetchall()
        if len(sql_res) != 0:
            cur.close()
            return jsonify({"result":"error", "msg":"duplicate nickname"}), 409
    cur.close()
    return jsonify({"result":"success", "msg":"no duplicate value"}), 200

@app.route("/register", methods=["POST"])
def Register():
    """유저 회원가입.

    Params:
        name `str`:
            회원의 실명.
        nickname `str`:
            회원의 별칭. nickname은 중복될 수 없음.
        email `str`:
            회원의 이메일(아이디). email은 중복될 수 없음.
        password `str`: 
            회원의 비밀번호. 
        phone `str`:
            회원의 전화번호. 중복 가능 여부는 아직 못정함.
    
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
    """
    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({"result":"error", "msg":"missing json in request"}), 400

    # POST로 인자 값 받아오기
    name = request.json.get("name")
    nickname = request.json.get("nickname")
    email = request.json.get("email")
    password = request.json.get("password")
    
    if not name:
        return jsonify({"result":"error", "msg":"missing name parameter"}), 400
    if not nickname:
        return jsonify({"result":"error", "msg":"missing nickname parameter"}), 400
    if not email:
        return jsonify({"result":"error", "msg":"missing email parameter"}), 400
    if not password:
        return jsonify({"result":"error", "msg":"missing password parameter"}), 400
    
    # DB 연결
    cur = mysql.connection.cursor()

    # 비밀번호 암호화
    password = password.encode("utf-8")
    hashed_pw = bcrypt.hashpw(password, bcrypt.gensalt())

    # 중복 체크
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql) 
    sql_res = cur.fetchall()
    if len(sql_res) != 0:
        cur.close()
        return jsonify({"result":"error", "msg":"duplicate email"}), 409
    
    sql = "SELECT * FROM UserInfo WHERE nickname='{}'".format(nickname)
    cur.execute(sql) 
    sql_res = cur.fetchall()
    if len(sql_res) != 0:
        cur.close()
        return jsonify({"result":"error", "msg":"duplicate nickname"}), 409


    # 유저 테이블에 데이터 삽입
    sql = "INSERT INTO UserInfo (email, password, name, nickname) VALUES (%s, %s, %s, %s)"
    cur.execute(sql, (email, hashed_pw, name, nickname))
    mysql.connection.commit()
    cur.close()
        
    return jsonify({"result":"success", "msg":"register"}), 200

@app.route("/protected", methods=["GET"])
@flask_jwt_extended.jwt_required()
def Protected():
    """유저 인증 함수
    
    이 함수는 JWT (JSON Web Token) 인증을 통해 사용자를 인증하고, 
    인증된 사용자의 정보를 반환한다.

    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        email `str`:
            사용자 이메일
        user `str`:
            사용자 닉네임
        name `str`:
            사용자 이름
    """
    currUserEmail = flask_jwt_extended.get_jwt_identity()

    # DB 안의 user 테이블 접근
    cur = mysql.connection.cursor()
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(currUserEmail)
    cur.execute(sql)
    sql_res = cur.fetchone()
    cur.close()

    if (sql_res == None):
        # user 테이블 내에 요청받은 email 데이터가 존재하지 않음
        return jsonify({"result":"error", "msg":"email does not exist"}), 422
    else:
        return jsonify({"result":"success", "msg":"user authentication", "email":currUserEmail, "user":sql_res["nickname"], "name":sql_res["name"]}), 200

# Connection refused 오류 발생
@app.route("/reset_password", methods=["POST"])
def ResetPassword():
    """비밀번호 초기화

    Params:
        email `str`:
            사용자의 email
    
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
    """
    # request 값이 올바르지 않은 경우
    if not request.is_json:
        return jsonify({"result":"error", "msg":"missing json in request"}), 400

    # POST로 인자 값 받아오기
    email = request.json.get("email")
    if not email:
        return jsonify({"result":"error", "msg":"missing email parameter"}), 400
    
    # DB 연결
    cur = mysql.connection.cursor()

    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    sql_res = cur.fetchone()
    if sql_res == None:
        cur.close()
        return jsonify({"result":"error", "msg":"email does not exist"}), 422
    else:
        # 무작위 문자 생성
        random_list = random.sample(string.ascii_letters, 8)
        random_pw = "".join(random_list)

        # 무작위 숫자 생성
        random_list = random.sample(string.digits, 3)
        random_pw = random_pw.join(random_list)

        # 무작위 특수문자 생성
        random_list = random.sample(string.punctuation, 1)
        random_pw = random_pw.join(random_list)

        # 비밀번호 암호화
        random_pw = random_pw.encode("utf-8")
        hashed_pw = bcrypt.hashpw(random_pw, bcrypt.gensalt())

        sql = "UPDATE UserInfo SET password=%s WHERE email=%s"
        cur.execute(sql, (hashed_pw, email))
        mysql.connection.commit()
        cur.close()

        msg = Message("비밀번호 초기화", sender="landpricekku@gmail.com", recipients=[email])
        msg.body = f"""새로운 비밀번호는 아래와 같습니다.

        PW: {random_pw}
        
        계정에 접속하여 비밀번호를 변경하실 것을 권장드립니다.
        감사합니다.
        """
        mail.send(msg)
        return jsonify({"result":"success", "msg":"password changed"}), 200

@app.route("/get_pnu", methods=["GET"])
def GetPNU():
    """입력된 좌표의 PNU 코드 조회
        
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
        pnu `str`:
            19자리 PNU 코드
        addressName `str`:
            토지 지번 주소
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    if not lat or not lng:
        return jsonify({"result":"error", "msg":"lat or lng parameter missing"}), 400
    pnu, address = get_pnu(float(lat), float(lng))
    if pnu == None or address == None:
        return jsonify({"result":"error", "msg":"PNU code for the requested coordinates does not exist"}), 422
    else:
        return jsonify({"result":"success", "msg":"get pnu", "pnu":pnu, "addressName":address}), 200

@app.route("/get_coord", methods=["GET"])
def GetWord():
    """입력된 주소의 좌표 조회

    Params:
        word `str`: 
            지번 주소
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        lat `float`:
            위도 좌표
        lng `float`:
            경도 좌표
        address `str`:
            지번 주소
    """
    word = request.args.get("word")
    if not word:
        return jsonify({"result":"error", "msg":"word parameter missing"}), 400
    lat, lng = get_word(word)
    if lat == None or lng == None:
        return jsonify({"result":"error", "msg":"address does not exist"}), 422
    else:
        return jsonify({"result":"success", "msg":"get address lat lng", "lat": lat, "lng": lng}), 200

@app.route("/get_land_info", methods=["GET"])
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
    if not lat or not lng:
        return jsonify({"result":"error", "msg":"lat or lng parameter missing"}), 400
    data = get_land_info(float(lat), float(lng))
    if data == None:
        return jsonify({"result":"error", "msg":"land information for the requested coordinates does not exist"}), 422
    else:
        return jsonify({"result":"success", "msg":"get land information", "data":data}), 200

@app.route("/get_bid_list", methods=["GET"])
def GetBidList():
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
        data `list`:
            법원 경매 데이터를 담은 리스트
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    zoom = request.args.get("zoom");
    if not lat or not lng:
        return jsonify({"result":"error", "msg":"lat or lng parameter missing"}), 400
    if not zoom:
        zoom = 2
    pnu, address = get_pnu(float(lat), float(lng))
    if pnu == None or address == None:
        return jsonify({"result":"error", "msg":"land bid list for the requested coordinates does not exist"}), 422
    
    if zoom == 1:
        pnu = pnu[0:2]
    else:
        pnu = pnu[0:5]

    cur = mysql.connect.cursor()
    sql = "SELECT * FROM Bid_LandList WHERE pnu LIKE '{}%'".format(pnu)
    cur.execute(sql)
    sql_res = cur.fetchall()

    for i in range(len(sql_res)):
        sql = "SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'".format(
            sql_res[i]["case_cd"], sql_res[i]["obj_nm"], sql_res[i]["court_in_charge"]
        )
        cur.execute(sql)
        case_info = cur.fetchone()

        lat, lng = get_word(sql_res[i]["addr"])
        sql_res[i]["lat"] = lat
        sql_res[i]["lng"] = lng
        sql_res[i]["case_info"] = case_info
        sql_res[i]["case_info"]["date_list"] = json.loads(sql_res[i]["case_info"]["date_list"])
        sql_res[i]["case_info"]["land_list"] = json.loads(sql_res[i]["case_info"]["land_list"])
    cur.close()
    return jsonify({"result":"success", "msg":"get bid list", "data":sql_res}), 200

@app.route("/get_bid", methods=["GET"])
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
        data `list`:
            법원 경매 데이터를 담은 리스트
    """
    pnu = request.args.get("pnu")
    if not pnu:
        return jsonify({"result":"error", "msg":"pnu parameter missing"}), 400

    cur = mysql.connect.cursor()
    sql = "SELECT * FROM Bid_LandList WHERE pnu='{}'".format(pnu)
    cur.execute(sql)
    sql_res = cur.fetchone()

    if sql_res == None:
        return jsonify({"result":"error", "msg":"bid data for the requested PNU code does not exist"}), 422

    sql = "SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'".format(
        sql_res["case_cd"], sql_res["obj_nm"], sql_res["court_in_charge"]
    )
    cur.execute(sql)
    case_info = cur.fetchone()
    sql_res["case_info"] = case_info
    sql_res["case_info"]["date_list"] = json.loads(sql_res["case_info"]["date_list"])
    sql_res["case_info"]["land_list"] = json.loads(sql_res["case_info"]["land_list"])
    cur.close()
    return jsonify({"result":"success", "msg":"get bid data", "data":sql_res}), 200

@app.route("/get_land_geometry", methods=["GET"])
def GetGeo():
    """연속지적도를 받아오는 함수

    종류: 2D 데이터API 2.0
    분류: 토지
    서비스명: 연속지적도
    서비스ID: LP_PA_CBND_BUBUN
    제공처: 국토교통부

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
        geometry `list`:
            연속지적도 데이터
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    pnu = request.args.get("pnu")
    if pnu:
        if lat or lng:
            return jsonify({"result":"error", "msg":"you cannot request pnu and coordinates at the same time"}), 400
    else:
        if not lat or not lng:
            return jsonify({"result":"error", "msg":"request parameter missing"}), 400
        else:
            pnu, address = get_pnu(float(lat), float(lng))

    # 엔드포인트
    endpoint = "http://api.vworld.kr/req/data"

    # 요청 파라미터
    service = "data"
    key = "FDA4D77C-C8E1-3870-8EF8-FBC5FF6F0204"
    req = "GetFeature"
    data = "LP_PA_CBND_BUBUN"
    page = 1
    size = 1000
    attrFilter = f"pnu:=:{pnu}"

    # 요청 URL
    url = f"{endpoint}?service={service}&request={req}&data={data}&key={key}&attrFilter={attrFilter}&page={page}&size={size}"
 
    # 요청 결과
    res = json.loads(requests.get(url).text)
    if (res["response"]["status"] == "NOT_FOUND"):
        return jsonify({"result":"error", "msg":"geometry data for the requested coordinates does not exist"}), 422
    # GeoJson 생성
    feature_collection = res["response"]["result"]["featureCollection"]
    return jsonify({"result":"success", "msg":"get land geometry data", "geometry":feature_collection["features"][0]["geometry"]["coordinates"]}), 200

@app.route("/get_sale_list", methods=["GET"])
def GetSaleList():
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
    if not lat or not lng:
        return jsonify({"result":"error", "msg":"lat or lng parameter missing"}), 400
    pnu, address = get_pnu(float(lat), float(lng))
    pnu = pnu[0:5]

    cur = mysql.connect.cursor()

    sql = """
        SELECT u.name, u.nickname, u.phone, l.pnu, l.lat, l.lng, 
        l.land_area, l.land_price, l.land_summary, l.reg_date 
        FROM UserInfo u, land_for_sale l 
        WHERE u.user_id=l.user_id
        AND l.pnu LIKE '{}%'
        """.format(pnu)
    cur.execute(sql)
    sql_res = cur.fetchall()
    cur.close()
    for i in range(len(sql_res)):
        land_response = get_land_info(float(sql_res[i]["lat"]), float(sql_res[i]["lng"]))
        sql_res[i]["land_info"] = land_response
        sql_res[i]["reg_date"] = sql_res[i]["reg_date"].strftime("%Y.%m.%d %H:%M")
    print(sql_res)
    return jsonify({"result":"error", "msg":"get land sale list", "data":sql_res}), 200

@app.route("/get_all_geo_data", methods=["GET"])
def GetAllGeoData():
    """연속지적도를 받아오는 함수

    종류: 2D 데이터API 2.0
    분류: 토지
    서비스명: 연속지적도
    서비스ID: LP_PA_CBND_BUBUN
    제공처: 국토교통부

    Params:
        lat `float`: 
            위도 좌표
        lng `float`: 
            경도 좌표
        level `int`:
            지도의 확대 레벨
    Returns:
        result `str`:
            응답 성공 여부 (success, error)
        msg `str`:
            응답 메시지
        geometry `list`:
            연속지적도 데이터
    """
    # 요청 파라미터 (변동되지 않음)
    service = "data"
    key = 'FDA4D77C-C8E1-3870-8EF8-FBC5FF6F0204'
    req = "GetFeature"
    page = 1
    size = 1000

    # 엔드포인트
    endpoint = "http://api.vworld.kr/req/data"

    lat = request.args.get("lat")
    lng = request.args.get("lng")
    level = request.args.get("level")
    if not lat or not lng or not level:
        return jsonify({"result":"error", "msg":"request parameter missing"}), 401
    pnu, address = get_pnu(float(lat), float(lng))
    level = int(level)

    # 시군구 경계 표시
    if level >= 6:
        data = "LT_C_ADSIGG_INFO"
        attrFilter = f"sig_cd:LIKE:{pnu[0:2]}"
        # 요청 URL
        url = f"{endpoint}?service={service}&request={req}&data={data}&key={key}&attrFilter={attrFilter}&page={page}&size={size}"
        
        # 요청 결과
        res = json.loads(requests.get(url).text)
        if (res["response"]["status"] == "NOT_FOUND"):
            return jsonify({"result":"error", "msg":"geometry data for the requested coordinates does not exist"}), 422
        feature_collection = res["response"]["result"]["featureCollection"]
        geo_dict = []
        cur = mysql.connect.cursor()

        # 사분위수 추출을 위한 리스트
        price_list = []
        priceIQR = {"Q1":0, "Q2":0, "Q3":0, "Q4":0}
        
        for i in range(len(feature_collection["features"])):
            sql = "SELECT avg(predict_land_price) as price, avg(predict_land_price/official_land_price) as percent FROM {}_LandInfo WHERE pnu LIKE '{}%'".format(
                region_code2name(pnu[0:2]), feature_collection["features"][i]["properties"]["sig_cd"]
            )
            cur.execute(sql)
            sql_res = cur.fetchall()
            geo_dict.append({
                "pnu":feature_collection["features"][i]["properties"]["sig_cd"],
                "geometry":feature_collection["features"][i]["geometry"]["coordinates"],
                "price":sql_res[0]["price"],
                "percent":sql_res[0]["percent"],
            })
            price_list.append(sql_res[0]["price"])
        price_list.sort()
        priceIQR["Q1"] = price_list[int(len(price_list) * 1/4)]
        priceIQR["Q2"] = price_list[int(len(price_list) * 2/4)]
        priceIQR["Q3"] = price_list[int(len(price_list) * 3/4)]
        priceIQR["Q4"] = price_list[len(price_list) - 1]
    # 읍면동 경계 표시
    elif 3 <= level <= 5:
        data = "LT_C_ADEMD_INFO"
        attrFilter = f"emd_cd:LIKE:{pnu[0:5]}"
        # 요청 URL
        url = f"{endpoint}?service={service}&request={req}&data={data}&key={key}&attrFilter={attrFilter}&page={page}&size={size}"
        
        # 요청 결과
        res = json.loads(requests.get(url).text)
        if (res["response"]["status"] == "NOT_FOUND"):
            return jsonify({"result":"error", "msg":"geometry data for the requested coordinates does not exist"}), 422
        feature_collection = res["response"]["result"]["featureCollection"]
        geo_dict = []
        cur = mysql.connect.cursor()

        # 사분위수 추출을 위한 리스트
        price_list = []
        priceIQR = {"Q1":0, "Q2":0, "Q3":0, "Q4":0}

        for i in range(len(feature_collection["features"])):
            sql = "SELECT avg(predict_land_price) as price, avg(predict_land_price/official_land_price) as percent FROM {}_LandInfo WHERE pnu LIKE '{}%'".format(
                region_code2name(pnu[0:2]), feature_collection["features"][i]["properties"]["emd_cd"]
            )
            cur.execute(sql)
            sql_res = cur.fetchall()
            geo_dict.append({
                "pnu":feature_collection["features"][i]["properties"]["emd_cd"],
                "geometry":feature_collection["features"][i]["geometry"]["coordinates"],
                "price":sql_res[0]["price"],
                "percent":sql_res[0]["percent"],
            })
            price_list.append(sql_res[0]["price"])
        price_list.sort()
        priceIQR["Q1"] = price_list[int(len(price_list) * 1/4)]
        priceIQR["Q2"] = price_list[int(len(price_list) * 2/4)]
        priceIQR["Q3"] = price_list[int(len(price_list) * 3/4)]
        priceIQR["Q4"] = price_list[len(price_list) - 1]
    # 세부 경계 표시
    else:
        data = "LP_PA_CBND_BUBUN"
        attrFilter = f"emdCd:=:{pnu[0:8]}"
        # 요청 URL
        url = f"{endpoint}?service={service}&request={req}&data={data}&key={key}&attrFilter={attrFilter}&page={page}&size={size}"
        
        # 요청 결과
        res = json.loads(requests.get(url).text)
        if (res["response"]["status"] == "NOT_FOUND"):
            return jsonify({"result":"error", "msg":"geometry data for the requested coordinates does not exist"}), 422
        feature_collection = res["response"]["result"]["featureCollection"]
        geo_dict = []
        cur = mysql.connect.cursor()

        # 사분위수 추출을 위한 리스트
        price_list = []
        priceIQR = {"Q1":0, "Q2":0, "Q3":0, "Q4":0}

        for i in range(len(feature_collection["features"])):
            sql = "SELECT predict_land_price as price, predict_land_price/official_land_price as percent FROM {}_LandInfo WHERE pnu='{}'".format(
                region_code2name(pnu[0:2]), feature_collection["features"][i]["properties"]["pnu"]
            )
            cur.execute(sql)
            sql_res = cur.fetchall()
            if len(sql_res) == 0:
                continue
            geo_dict.append({
                "pnu":feature_collection["features"][i]["properties"]["pnu"],
                "geometry":feature_collection["features"][i]["geometry"]["coordinates"],
                "price":sql_res[0]["price"],
                "percent":sql_res[0]["percent"],
            })
            price_list.append(sql_res[0]["price"])
        price_list.sort()
        priceIQR["Q1"] = price_list[int(len(price_list) * 1/4)]
        priceIQR["Q2"] = price_list[int(len(price_list) * 2/4)]
        priceIQR["Q3"] = price_list[int(len(price_list) * 3/4)]
        priceIQR["Q4"] = price_list[len(price_list) - 1]
    return jsonify({"result":"success", "msg":"get all land grometry data", "data":geo_dict, "priceIQR":priceIQR}), 200




@app.route("/land_like", methods=["POST"])
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
    cur = mysql.connect.cursor()

    # 유저의 고유번호(id) 불러오기
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    userData = cur.fetchall()

    # 해당 email이 데이터베이스에 존재하지 않을 경우
    if len(userData) == 0:
        return jsonify({"result":"error", "msg":"email does not exist"}), 401
    
    userId = userData[0]["user_id"]


    # 토지의 위경도 값을 PNU 코드로 변경
    lat = request.json.get("lat")
    lng = request.json.get("lng")
    pnu, address = get_pnu(lng, lat)

    # 좋아요 여부 확인
    sql = "SELECT * FROM land_like WHERE user_id='{}' AND pnu='{}'".format(userId, pnu)
    cur.execute(sql)
    likeData = cur.fetchall()
    cur.close()

    # land_like DB에 해당 유저의 좋아요 데이터가 없을 경우 (좋아요)
    if len(likeData) == 0:
        cur = mysql.connection.cursor()
        sql = "INSERT INTO land_like (user_id, pnu, lat, lng) VALUES ({}, '{}', {}, {});".format(
            userId, pnu, lat, lng
        )
        cur.execute(sql)
        mysql.connection.commit()
        cur.close()
        return jsonify({"result":"success", "msg":"like"}), 200
    # 이미 land_like DB에 해당 유저의 좋아요 데이터가 있을 경우 (좋아요 해제)
    else:
        cur = mysql.connection.cursor()
        sql = "DELETE FROM land_like WHERE user_id='{}' AND pnu='{}';".format(userId, pnu)
        cur.execute(sql)
        mysql.connection.commit()
        cur.close()
        return jsonify({"result":"success", "msg":"unlike"}), 200

@app.route("/load_land_like", methods=["POST"])
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
    cur = mysql.connect.cursor()

    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(lng, lat)

    # 좋아요 목록 불러오기
    sql = "SELECT * FROM land_like WHERE pnu='{}'".format(pnu)
    cur.execute(sql)
    likeData = cur.fetchall()

    totalLikeCount = len(likeData)
    isLike = False
    print(email)
    print("a")
    
    # 유저의 고유번호(id) 불러오기
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    userData = cur.fetchall()
    

    if len(userData) != 0:
        userId = userData[0]["user_id"]
        print(userId)
        for i in range(totalLikeCount):
            if (likeData[i]["user_id"] == userId):
                isLike = True
    
    return jsonify(total_like=totalLikeCount, is_like=isLike), 200

@app.route("/user_land_like_list", methods=["POST"])
def UserLandLikeList():
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
    cur = mysql.connect.cursor()

    # 유저의 고유번호(id) 불러오기
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    userData = cur.fetchall()

    # 해당 이메일로 유저가 조회되지 않을 경우
    if len(userData) == 0:
        return jsonify({'result':'error', 'msg':'user dose not found'}), 401
    
    userId = userData[0]["user_id"]
        
    # 좋아요 목록 불러오기
    sql = "SELECT * FROM land_like WHERE user_id={}".format(userId)
    cur.execute(sql)
    likeData = cur.fetchall()

    landList = []

    for i in range(len(likeData)):
        landResponse = GetLandInfo(likeData[i]["lng"], likeData[i]["lat"])[0].json
        landResponse["feature"]["lat"] = likeData[i]["lat"]
        landResponse["feature"]["lng"] = likeData[i]["lng"]
        landList.append(landResponse["feature"])
    
    return jsonify(land_like=landList), 200


@app.route("/reg_land_for_sale", methods=["POST"])
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
    cur = mysql.connection.cursor()

    # 유저의 고유번호(id) 불러오기
    sql = f"SELECT * FROM UserInfo WHERE email='{email}'"
    cur.execute(sql)
    user_data = cur.fetchone()
    print(user_data)

    # 해당 email이 데이터베이스에 존재하지 않을 경우
    if user_data == None:
        return jsonify({"result":"error", "msg":"email does not exist"}), 401
    
    user_id = user_data["user_id"]

    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(float(lat), float(lng))

    # 매물 등록 여부 확인
    sql = f"SELECT * FROM land_for_sale WHERE pnu='{pnu}'"
    cur.execute(sql)
    land_data = cur.fetchone()
    print(land_data)

    # land_for_sale DB에 해당 토지의 매물 데이터가 없을 경우
    if land_data == None:
        land_area = request.json.get("land_area")
        land_price = request.json.get("land_price")
        land_summary = request.json.get("land_summary")

        sql = "INSERT INTO land_for_sale (pnu, user_id, lat, lng, land_area, land_price, land_summary) VALUES (%s, %s, %s, %s, %s, %s, %s)"
        print(sql)
        cur.execute(sql, (pnu, user_id, lat, lng, land_area, land_price, land_summary))
        mysql.connection.commit()
        cur.close()
        return jsonify({"result":"success", "msg":"register"}), 200
    # 이미 land_like DB에 해당 유저의 좋아요 데이터가 있을 경우 (좋아요 해제)
    else:
        if land_data["user_id"] == user_id:
            sql = "DELETE FROM land_owner WHERE user_id='{}' AND pnu='{}';".format(userId, pnu)
            cur.execute(sql)
            mysql.connection.commit()
            cur.close()
            return jsonify({"result":"success", "msg":"deregister"}), 200
        else:
            return jsonify({"result":"error", "msg":"already register"}), 422

@app.route("/dereg_land_for_sale", methods=["POST"])
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
    cur = mysql.connect.cursor()

    # 유저의 고유번호(id) 불러오기
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    userData = cur.fetchall()

    # 해당 email이 데이터베이스에 존재하지 않을 경우
    if len(userData) == 0:
        return jsonify({"result":"error", "msg":"email does not exist"}), 401
    
    userId = userData[0]["user_id"]


    # 토지의 위경도 값을 PNU 코드로 변경
    lat = float(request.json.get("lat"))
    lng = float(request.json.get("lng"))
    pnu, address = get_pnu(lng, lat)

    # 매물 등록 여부 확인
    sql = "SELECT * FROM land_for_sale WHERE pnu='{}'".format(pnu)
    cur.execute(sql)
    landData = cur.fetchall()
    cur.close()


    # land_for_sale DB에 해당 토지의 매물 데이터가 없을 경우
    if len(landData) != 0:
        cur = mysql.connection.cursor()
        sql = "DELETE FROM land_for_sale WHERE user_id='{}' AND pnu='{}';".format(userId, pnu)
        cur.execute(sql)
        mysql.connection.commit()
        cur.close()
        return jsonify({"result":"success", "msg":"deregister"}), 200

@app.route("/user_land_for_sale_list", methods=["POST"])
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
    cur = mysql.connect.cursor()

    # 유저의 고유번호(id) 불러오기
    sql = "SELECT * FROM UserInfo WHERE email='{}'".format(email)
    cur.execute(sql)
    userData = cur.fetchall()

    # 해당 이메일로 유저가 조회되지 않을 경우
    if len(userData) == 0:
        return jsonify({'result':'error', 'msg':'user dose not found'}), 401
    
    userId = userData[0]["user_id"]
        
    # 좋아요 목록 불러오기
    sql = "SELECT * FROM land_for_sale WHERE user_id={}".format(userId)
    cur.execute(sql)
    sql_res = cur.fetchall()

    for i in range(len(sql_res)):
        land_response = get_land_info(float(sql_res[i]["lat"]), float(sql_res[i]["lng"]))
        sql_res[i]["land_info"] = land_response
        sql_res[i]["reg_date"] = sql_res[i]["reg_date"].strftime("%Y.%m.%d %H:%M")
    
    return jsonify(land_for_sale=sql_res), 200

@app.route("/load_addr_csv", methods=["GET"])
def LoadAddrCsv():
    f = open(WORKSPACE + "data/pnu_code.csv", "r", encoding="utf-8")
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
    return jsonify({"result":"success", "msg":"load address csv data", "data":data}), 200

if __name__ == "__main__":
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS)
    ssl_context.load_cert_chain(certfile="/home/students/cs/202120990/server/SSL/fullchain.pem", keyfile="/home/students/cs/202120990/server/SSL/privkey.pem", password="csserver8403598*")
    app.run(host="222.116.135.166", port="5001", ssl_context=ssl_context, debug=True)