from app import db
from app.models.land import LandInfo, LandReport, LandProperty
from app.models.user import Users
from app.functions.pnu_geolocation_lookup import get_pnu, get_word, region_code2name
from app.functions.predict import pred
from app.functions.text_generate import generate
from app.functions.convert_code import code2addr
from app.functions.get_bid_data import get_bid_land_list_data, get_bid_case_data
from app.functions.api import LandFeatureAPI, LandUsePlanAPI
from config import api
from datetime import datetime
import json
import pytz

def get_land_data(pnu) -> dict:
    """위경도 값으로 토지 정보 받아오기

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
    address = code2addr(pnu)
    if pnu == None or address == None:
        return None

    main_num = pnu[11:15]
    for i in range(len(main_num)):
        if main_num[i] != "0":
            if (i >=3):
                main_num = "000"
                break
            main_num = main_num[0:i+1]
            break
    
    land_info = LandInfo[pnu[0:2]].query.filter_by(pnu=pnu).first()
    if not land_info:
        land = {}
        # 데이터 채워넣기
        land["pnu"] = pnu
        target_year = datetime.now(pytz.timezone("Asia/Seoul")).year
        land["predict_land_price"] = None
        land["last_predicted_date"] = None

        # Get land feature data
        lf_api = LandFeatureAPI(api.LAND_API_KEY)
        result = lf_api.get_data(pnu, target_year)
        if result == None:
            return None

        land["official_land_price"] = result["pblntfPclnd"]
        land["land_classification"] = result["lndcgrCodeNm"]
        land["land_area"] = result["lndpclAr"]
        land["land_register"] = result["regstrSeCodeNm"]
        land["land_zoning"] = result["prposArea1Nm"]
        land["land_use_situation"] = result["ladUseSittnNm"]
        land["land_height"] = result["tpgrphHgCodeNm"]
        land["land_form"] = result["tpgrphFrmCodeNm"]
        land["road_side"] = result["roadSideCodeNm"]
        land["land_feature_stdr_year"] = result["stdrYear"]

        lup_api = LandUsePlanAPI(api.LAND_API_KEY)
        land["land_uses"] = lup_api.get_data(pnu, return2name=True)
        if land["land_uses"] == None:
            land["land_uses"] = "없음"

        new_land = LandInfo[pnu[0:2]](**land)
        db.session.add(new_land)
        db.session.commit()

        bid_data = _get_bid_data(pnu)
        land_property_data = _get_land_property_data(pnu)
        return {
        "pnu": pnu,
        "addr": address,
        "land_info": {
            "official_land_price": land["official_land_price"],
            "predict_land_price": land["predict_land_price"],
            "land_classification": land["land_classification"],
            "land_zoning": land["land_zoning"],
            "land_use_situation": land["land_use_situation"],
            "land_register": land["land_register"],
            "land_area": land["land_area"],
            "land_height": land["land_height"],
            "land_form": land["land_form"],
            "road_side": land["road_side"],
            "land_uses": land["land_uses"],
        },
        "last_predicted_date": datetime.now(pytz.timezone('Asia/Seoul')).strftime("%Y-%m-%d"),
        "land_feature_stdr_year": land["land_feature_stdr_year"],
        "land_trade_list": [],
        "bid_data": bid_data,
        "land_property_data": land_property_data,
        "total_like": 0,
    }
    bid_data = _get_bid_data(pnu)
    land_property_data = _get_land_property_data(pnu)
    print({
        "pnu": pnu,
        "addr": address,
        "land_info": {
            "official_land_price": land_info.official_land_price,
            "predict_land_price": land_info.predict_land_price,
            "land_classification": land_info.land_classification,
            "land_zoning": land_info.land_zoning,
            "land_use_situation": land_info.land_use_situation,
            "land_register": land_info.land_register,
            "land_area": land_info.land_area,
            "land_height": land_info.land_height,
            "land_form": land_info.land_form,
            "road_side": land_info.road_side,
            "land_uses": land_info.land_uses,
        },
        "last_predicted_date": land_info.last_predicted_date.strftime("%Y-%m-%d") if land_info.last_predicted_date else None,
        "land_feature_stdr_year": land_info.land_feature_stdr_year,
        "land_trade_list": [],
        "bid_data": bid_data,
        "land_property_data": land_property_data,
        "total_like": 0,
    })
    return {
        "pnu": pnu,
        "addr": address,
        "land_info": {
            "official_land_price": land_info.official_land_price,
            "predict_land_price": land_info.predict_land_price,
            "land_classification": land_info.land_classification,
            "land_zoning": land_info.land_zoning,
            "land_use_situation": land_info.land_use_situation,
            "land_register": land_info.land_register,
            "land_area": land_info.land_area,
            "land_height": land_info.land_height,
            "land_form": land_info.land_form,
            "road_side": land_info.road_side,
            "land_uses": land_info.land_uses,
        },
        "last_predicted_date": land_info.last_predicted_date.strftime("%Y-%m-%d") if land_info.last_predicted_date else None,
        "land_feature_stdr_year": land_info.land_feature_stdr_year,
        "land_trade_list": [],
        "bid_data": bid_data,
        "land_property_data": land_property_data,
        "total_like": 0,
    }

def set_land_predict_price_data(pnu):
    land_info = LandInfo[pnu[0:2]].query.filter_by(pnu=pnu).first()
    if not land_info:
        # 예외처리 해야함
        return None
    target_year = datetime.now(pytz.timezone("Asia/Seoul")).year
    target_month = datetime.now(pytz.timezone("Asia/Seoul")).month
    predict_land_price = str(pred(pnu, target_year, target_month))
    land_info.predict_land_price = predict_land_price
    land_info.last_predicted_date = datetime.now(pytz.timezone("Asia/Seoul"))
    db.session.commit()

def _get_bid_data(pnu: str):
    data = get_bid_land_list_data(pnu[0:2], pnu[2:5])
    if data != None:
        for d in data:
            if d["pnu"] == pnu:
                lat, lng = get_word(d["addr"]["address"])
                case_info = get_bid_case_data(d["court_in_charge"], d["case_cd"], d["obj_nm"])
                d["lat"] = lat
                d["lng"] = lng
                d["case_info"] = case_info
                d["case_info"]["date_list"] = json.loads(d["case_info"]["date_list"])
                d["case_info"]["land_list"] = json.loads(d["case_info"]["land_list"])
                
                return d
    return None

def _get_land_property_data(pnu: str):
    land_property_data = LandProperty.query.filter_by(pnu=pnu).first()
    if not land_property_data:
        return None
    else:
        user = Users.query.filter_by(user_id=land_property_data.user_id).first()
        data = {
            "pnu": land_property_data.pnu,
            "user_id": land_property_data.user_id,
            "lat": land_property_data.lat,
            "lng": land_property_data.lng,
            "land_area": land_property_data.area,
            "land_price": land_property_data.price,
            "land_summary": land_property_data.summary,
            "nickname": user.nickname if user else "알수없음"  # 유저가 없을 경우 None 처리
        }
        return data

def get_land_report_data(pnu):
    pnu_prefix = pnu[:2]
    if pnu_prefix in LandInfo:
        LandInfoModel = LandInfo[pnu_prefix]
        land_info = LandInfoModel.query.filter_by(pnu=pnu).first()
        if land_info.predict_land_price != None:
            land_report = LandReport.query.filter_by(pnu=pnu).first()
    
            if not land_report:
                gen_text = generate(pnu, land_info.predict_land_price)
                new_land_report = LandReport(pnu=pnu, report=gen_text)
                db.session.add(new_land_report)
                db.session.commit()
                return gen_text
            return land_report.report
        else:
            None
    else:
        None