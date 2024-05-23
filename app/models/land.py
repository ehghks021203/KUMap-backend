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
    last_predicted_date = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Seoul')), onupdate=lambda: datetime.now(pytz.timezone('Asia/Seoul')))
    land_feature_stdr_year = db.Column(db.Integer)

    def __repr__(self):
        return f"<LandInfo {self.pnu}>"

def LandInfoFactory(table_name):
    class LandInfo(AbstractLandInfo):
        __tablename__ = table_name
        __table_args__ = {'extend_existing': True}
    return LandInfo

LandInfo = {
    "11": LandInfoFactory("11_land_info"),
    "26": LandInfoFactory("26_land_info")
}