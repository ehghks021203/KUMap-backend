from app import db
from datetime import datetime
import pytz

class AbstractLandInfo(db.Model):
    __abstract__ = True

    pnu = db.Column(db.String(20), primary_key=True)
    official_land_price = db.Column(db.Float)
    predict_land_price = db.Column(db.Float)
    land_classification = db.Column(db.String(10))
    land_zoning = db.Column(db.String(20))
    land_use_situation = db.Column(db.String(20))
    land_register = db.Column(db.String(10))
    land_area = db.Column(db.Float)
    land_height = db.Column(db.String(10))
    land_form = db.Column(db.String(10))
    road_side = db.Column(db.String(10))
    land_uses = db.Column(db.String)
    last_predicted_date = db.Column(db.TIMESTAMP, nullable=True)
    land_feature_stdr_year = db.Column(db.Integer)

    def __repr__(self):
        return f"<LandInfo {self.pnu}>"

def LandInfoFactory(table_name):
    class_name = f"LandInfo_{table_name}"
    return type(class_name, (AbstractLandInfo,), {"__tablename__": table_name, "__table_args__": {'extend_existing': True}})

LandInfo = {
    "11": LandInfoFactory("11_land_info"),
    "26": LandInfoFactory("26_land_info"),
    "27": LandInfoFactory("27_land_info"), 
    "28": LandInfoFactory("28_land_info"), 
    "29": LandInfoFactory("29_land_info"), 
    "30": LandInfoFactory("30_land_info"), 
    "31": LandInfoFactory("31_land_info"), 
    "36": LandInfoFactory("36_land_info"), 
    "41": LandInfoFactory("41_land_info"), 
    "43": LandInfoFactory("43_land_info"), 
    "44": LandInfoFactory("44_land_info"), 
    "46": LandInfoFactory("46_land_info"), 
    "47": LandInfoFactory("47_land_info"), 
    "48": LandInfoFactory("48_land_info"), 
    "50": LandInfoFactory("50_land_info"), 
    "51": LandInfoFactory("51_land_info"), 
    "52": LandInfoFactory("52_land_info")
}

class LandProperty(db.Model):
    __tablename__ = "land_property"

    pnu = db.Column(db.String(20), primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.user_id"), nullable=False)
    lat = db.Column(db.Numeric(17, 14), nullable=False)
    lng = db.Column(db.Numeric(17, 14), nullable=False)
    area = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    reg_date = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Seoul')))

    def __repr__(self):
        return f"<LandProperty pnu={self.pnu} user_id={self.user_id}>"


class LandReport(db.Model):
    __tablename__ = "land_report"

    pnu = db.Column(db.String(20), primary_key=True)
    report = db.Column(db.Text, nullable=False)
    gen_date = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Seoul')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Seoul')))

    def __repr__(self):
        return f"<LandReport(pnu='{self.pnu}', gen_date='{self.gen_date}')>"

class RegionCoordinates(db.Model):
    __tablename__ = "region_coordinates"

    pnu = db.Column(db.String(10), primary_key=True)
    type = db.Column(db.String(12), nullable=False)
    region = db.Column(db.String(50), nullable=False)
    lat = db.Column(db.Numeric(17, 14), nullable=False)
    lng = db.Column(db.Numeric(17, 14), nullable=False)

    def __repr__(self):
        return f"<RegionCoordinates(pnu='{self.pnu}')>"