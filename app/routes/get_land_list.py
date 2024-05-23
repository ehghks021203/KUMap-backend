from app.functions.pnu_geolocation_lookup import get_pnu, get_word
from app.functions.get_land_data import get_land_data

from flask import Blueprint, request, jsonify
import json

get_land_list_routes = Blueprint("get_land_list", __name__)


@get_land_list_routes.route("/get_bid_list", methods=["GET"])
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
        err_code `str`:
            오류 코드 (API_GUIDE.md 참고)
        data `list`:
            법원 경매 데이터를 담은 리스트
    """
    lat = request.args.get("lat")
    lng = request.args.get("lng")
    zoom = request.args.get("zoom")

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
        pnu = pnu[0:2]
    else:
        pnu = pnu[0:5]

    db = Database()
    print(pnu)

    q = """
        SELECT * FROM Bid_LandList WHERE pnu LIKE %s
        """
    print(q)
    sql_res = db.executeAll(q, (f"{pnu}%"))
    for i in range(len(sql_res)):
        q = """
            SELECT * FROM Bid_CaseList WHERE case_cd='{}' AND obj_nm={} AND court_in_charge='{}'
            """.format(sql_res[i]["case_cd"], sql_res[i]["obj_nm"], sql_res[i]["court_in_charge"])
        case_info = db.executeOne(q)
        lat, lng = get_word(sql_res[i]["addr"])
        sql_res[i]["lat"] = lat
        sql_res[i]["lng"] = lng
        sql_res[i]["case_info"] = case_info
        sql_res[i]["case_info"]["date_list"] = json.loads(sql_res[i]["case_info"]["date_list"])
        sql_res[i]["case_info"]["land_list"] = json.loads(sql_res[i]["case_info"]["land_list"])
    
    return jsonify({
        "result":"success", 
        "msg":"get bid list",
        "err_code":"00",
        "data":sql_res
    }), 200

@get_land_list_routes.route("/get_sale_list", methods=["GET"])
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

    # Error: 파라미터 값이 비어있거나 없음
    if not lat or not lng:
        return jsonify({
            "result":"error", 
            "msg":"lat or lng parameter missing",
            "err_code":"11"
        }), 400
    pnu, address = get_pnu(float(lat), float(lng))
    pnu = pnu[0:5]

    db = Database()

    q = """
        SELECT u.name, u.nickname, u.phone, l.pnu, l.lat, l.lng, l.land_area, l.land_price, l.land_summary, l.reg_date 
        FROM UserInfo u, land_for_sale l 
        WHERE u.user_id=l.user_id
        AND l.pnu LIKE %s
        """
    sql_res = db.executeAll(q, (f"{pnu}%"))
    for i in range(len(sql_res)):
        land_response = get_land_data(float(sql_res[i]["lat"]), float(sql_res[i]["lng"]))
        sql_res[i]["land_info"] = land_response
        sql_res[i]["reg_date"] = sql_res[i]["reg_date"].strftime("%Y.%m.%d %H:%M")
    
    return jsonify({
        "result":"error", 
        "msg":"get land sale list", 
        "err_code":"00",
        "data":sql_res
    }), 200

'''
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

'''
