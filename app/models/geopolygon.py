from app import db
from datetime import datetime
import pytz

class GeometryData(db.Model):
    __tablename__ = "geometry_data"

    pnu = db.Column(db.String(10), primary_key=True)
    centroid_lat = db.Column(db.Numeric(17, 14), nullable=False)
    centroid_lng = db.Column(db.Numeric(17, 14), nullable=False)
    multi_polygon = db.Column(db.dialects.mysql.LONGTEXT)
    
    def __repr__(self):
        return f"<GeometryData {self.pnu}>"
