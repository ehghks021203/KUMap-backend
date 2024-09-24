"""=========================================================================================
<region_marker.py> (수정해야함)

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
from app.utils.decorators import *
from app.utils.exceptions import *
from app.functions.convert_code import code2addr_dict, code2addr
from app.functions.pnu_geolocation_lookup import get_word
from app.utils.types import MapZoomLevel
from app.models.land import *

region_marker_routes = Blueprint("region_marker", __name__)


@region_marker_routes.route("/get_region_markers", methods=["GET"])
@error_handler()
def get_region_markers():
    validate_args_params("lat1", "lng1", "lat2", "lng2", "zoom")
    lat1 = request.args.get("lat1")
    lng1 = request.args.get("lng1")
    lat2 = request.args.get("lat2")
    lng2 = request.args.get("lng2")
    zoom = int(request.args.get("zoom"))
    
    t = "eupmyeondong"
    if zoom in MapZoomLevel.HIGH:
        t = "sigungu"
    elif zoom in MapZoomLevel.TOP:
        t = "sido"

    items = RegionCoordinates.query.filter(
        db.and_(
            RegionCoordinates.lat.between(lat1, lat2), 
            RegionCoordinates.lng.between(lng1, lng2),
            RegionCoordinates.type == t
            )
        ).all()
    data = []
    for item in items:
        pnu_prefix = item.pnu[:2]
        if pnu_prefix in LandInfo:
            LandInfoModel = LandInfo[pnu_prefix]

            avg_price = db.session.query(
                db.func.avg(LandInfoModel.predict_land_price)
            ).filter(LandInfoModel.pnu.like(f"{item.pnu}%")).scalar()

            avg_price = avg_price if avg_price is not None else 0

            non_null_or_zero_count = db.session.query(
                db.func.count(LandInfoModel.pnu)
            ).filter(
                LandInfoModel.pnu.like(f"{item.pnu}%"),
                LandInfoModel.predict_land_price.isnot(None),
                LandInfoModel.predict_land_price != 0
            ).scalar()

            # 공식 가격 대비 예측 가격의 비율 계산
            price_ratio = 0
            if avg_price and avg_price != 0:
                official_price = db.session.query(
                    db.func.avg(LandInfoModel.official_land_price)
                ).filter(LandInfoModel.pnu.like(f"{item.pnu}%")).scalar()
                if official_price and official_price != 0:
                    price_ratio = avg_price / official_price * 100

            data.append({
                "pnu": item.pnu,
                "address": code2addr(item.pnu),
                "region": item.region,
                "lat": item.lat,
                "lng": item.lng,
                "avg_predict_land_price": f"{avg_price:.0f}",
                "price_ratio": f"{price_ratio:.2f}",
                "total_land_count": non_null_or_zero_count
            })
        
    return jsonify({
            "result":"success", 
            "msg":"get region marker", 
            "err_code":"00",
            "data":data
        }), 200

@region_marker_routes.route("/get_region_marker", methods=["GET"])
@error_handler()
def _get_region_marker():
    validate_args_params("lat1", "lng1", "lat2", "lng2", "zoom")
    lat1 = request.args.get("lat1")
    lng1 = request.args.get("lng1")
    lat2 = request.args.get("lat2")
    lng2 = request.args.get("lng2")
    zoom = int(request.args.get("zoom"))
    
    t = "eupmyeondong"
    if zoom in MapZoomLevel.HIGH:
        t = "sigungu"
    elif zoom in MapZoomLevel.TOP:
        t = "sido"

    items = RegionCoordinates.query.filter(
        db.and_(
            RegionCoordinates.lat.between(lat1, lat2), 
            RegionCoordinates.lng.between(lng1, lng2),
            RegionCoordinates.type == t
            )
        ).all()
    data = []
    for item in items:
        pnu_prefix = item.pnu[:2]
        if pnu_prefix in LandInfo:
            LandInfoModel = LandInfo[pnu_prefix]

            avg_price = db.session.query(
                db.func.avg(LandInfoModel.predict_land_price)
            ).filter(LandInfoModel.pnu.like(f"{item.pnu}%")).scalar()

            avg_price = avg_price if avg_price is not None else 0

            non_null_or_zero_count = db.session.query(
                db.func.count(LandInfoModel.pnu)
            ).filter(
                LandInfoModel.pnu.like(f"{item.pnu}%"),
                LandInfoModel.predict_land_price.isnot(None),
                LandInfoModel.predict_land_price != 0
            ).scalar()

            # 공식 가격 대비 예측 가격의 비율 계산
            price_ratio = 0
            if avg_price and avg_price != 0:
                official_price = db.session.query(
                    db.func.avg(LandInfoModel.official_land_price)
                ).filter(LandInfoModel.pnu.like(f"{item.pnu}%")).scalar()
                if official_price and official_price != 0:
                    price_ratio = avg_price / official_price * 100

            data.append({
                "pnu": item.pnu,
                "addr": code2addr(item.pnu),
                "region": item.region,
                "lat": item.lat,
                "lng": item.lng,
                "avg_predict_land_price": f"{avg_price:.0f}",
                "price_ratio": f"{price_ratio:.2f}",
                "total_land_count": non_null_or_zero_count
            })
        
    return jsonify({
            "result":"success", 
            "msg":"get region marker", 
            "err_code":"00",
            "data":data
        }), 200

@region_marker_routes.route("/get_region_land_describes", methods=["GET"])
@error_handler()
def get_region_land_describes():
    validate_args_params("pnu")
    pnu = request.args.get("pnu")
    pnu_prefix = pnu[:2]

    region_data = RegionCoordinates.query.filter_by(pnu=pnu).first()

    if pnu_prefix in LandInfo:
        LandInfoModel = LandInfo[pnu_prefix]

        avg_price = db.session.query(
            db.func.avg(LandInfoModel.predict_land_price)
        ).filter(LandInfoModel.pnu.like(f"{pnu}%")).scalar()

        avg_price = avg_price if avg_price is not None else 0

        non_null_or_zero_count = db.session.query(
            db.func.count(LandInfoModel.pnu)
        ).filter(
            LandInfoModel.pnu.like(f"{pnu}%"),
            LandInfoModel.predict_land_price.isnot(None),
            LandInfoModel.predict_land_price != 0
        ).scalar()

        # 공식 가격 대비 예측 가격의 비율 계산
        price_ratio = 0
        if avg_price and avg_price != 0:
            official_price = db.session.query(
                db.func.avg(LandInfoModel.official_land_price)
            ).filter(LandInfoModel.pnu.like(f"{pnu}%")).scalar()
            if official_price and official_price != 0:
                price_ratio = avg_price / official_price * 100

        # 상위 10개의 predict_land_price 데이터를 가져오는 쿼리
        top_10_ratios = db.session.query(
            LandInfoModel.pnu,
            LandInfoModel.predict_land_price,
            LandInfoModel.official_land_price,
            (LandInfoModel.predict_land_price / LandInfoModel.official_land_price).label('price_ratio')
        ).filter(
            LandInfoModel.pnu.like(f"{pnu}%"),
            LandInfoModel.predict_land_price.isnot(None),
            LandInfoModel.predict_land_price != 0
        ).order_by(
            db.desc('price_ratio')
        ).limit(10).all()

        # top_10_ratios 데이터를 처리하여 JSON으로 반환할 수 있도록 준비
        top_10_ratios_data = []
        for item in top_10_ratios:
            addr = code2addr_dict(item.pnu)
            lat, lng = get_word(addr["address"])
            top_10_ratios_data.append({
                "pnu": item.pnu,
                "address": addr,
                "predict_land_price": item.predict_land_price,
                "official_land_price": item.official_land_price,
                "price_ratio": f"{item.price_ratio * 100:.2f}",  # 비율을 백분율로 변환
                "lat": lat,
                "lng": lng
            })

        data = {
            "pnu": pnu,
            "region": code2addr(pnu),
            "lat": region_data.lat,
            "lng": region_data.lng,
            "avg_predict_land_price": f"{avg_price:.0f}",
            "price_ratio": f"{price_ratio:.2f}",
            "total_land_count": non_null_or_zero_count,
            "land": top_10_ratios_data
        }
    return jsonify({
            "result":"success", 
            "msg":"get region describe", 
            "err_code":"00",
            "data":data
        }), 200

@region_marker_routes.route("/get_region_describe", methods=["GET"])
@error_handler()
def _get_region_describe():
    validate_args_params("pnu")
    pnu = request.args.get("pnu")
    pnu_prefix = pnu[:2]

    region_data = RegionCoordinates.query.filter_by(pnu=pnu).first()

    if pnu_prefix in LandInfo:
        LandInfoModel = LandInfo[pnu_prefix]

        avg_price = db.session.query(
            db.func.avg(LandInfoModel.predict_land_price)
        ).filter(LandInfoModel.pnu.like(f"{pnu}%")).scalar()

        avg_price = avg_price if avg_price is not None else 0

        non_null_or_zero_count = db.session.query(
            db.func.count(LandInfoModel.pnu)
        ).filter(
            LandInfoModel.pnu.like(f"{pnu}%"),
            LandInfoModel.predict_land_price.isnot(None),
            LandInfoModel.predict_land_price != 0
        ).scalar()

        # 공식 가격 대비 예측 가격의 비율 계산
        price_ratio = 0
        if avg_price and avg_price != 0:
            official_price = db.session.query(
                db.func.avg(LandInfoModel.official_land_price)
            ).filter(LandInfoModel.pnu.like(f"{pnu}%")).scalar()
            if official_price and official_price != 0:
                price_ratio = avg_price / official_price * 100

        # 상위 10개의 predict_land_price 데이터를 가져오는 쿼리
        top_10_ratios = db.session.query(
            LandInfoModel.pnu,
            LandInfoModel.predict_land_price,
            LandInfoModel.official_land_price,
            (LandInfoModel.predict_land_price / LandInfoModel.official_land_price).label('price_ratio')
        ).filter(
            LandInfoModel.pnu.like(f"{pnu}%"),
            LandInfoModel.predict_land_price.isnot(None),
            LandInfoModel.predict_land_price != 0
        ).order_by(
            db.desc('price_ratio')
        ).limit(10).all()

        # top_10_ratios 데이터를 처리하여 JSON으로 반환할 수 있도록 준비
        top_10_ratios_data = []
        for item in top_10_ratios:
            addr = code2addr_dict(item.pnu)
            lat, lng = get_word(addr["address"])
            top_10_ratios_data.append({
                "pnu": item.pnu,
                "addr": addr,
                "predict_land_price": item.predict_land_price,
                "official_land_price": item.official_land_price,
                "price_ratio": f"{item.price_ratio * 100:.2f}",  # 비율을 백분율로 변환
                "lat": lat,
                "lng": lng
            })

        data = {
            "pnu": pnu,
            "region": code2addr(pnu),
            "lat": region_data.lat,
            "lng": region_data.lng,
            "avg_predict_land_price": f"{avg_price:.0f}",
            "price_ratio": f"{price_ratio:.2f}",
            "total_land_count": non_null_or_zero_count,
            "land": top_10_ratios_data
        }
    return jsonify({
            "result":"success", 
            "msg":"get region describe", 
            "err_code":"00",
            "data":data
        }), 200