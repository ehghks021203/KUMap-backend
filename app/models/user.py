from app import db
from datetime import datetime
import pytz

class Users(db.Model):
    __tablename__ = "users"

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_role = db.Column(db.Integer, nullable=False, default=1)
    email = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(20), nullable=False)
    nickname = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20))
    created_at = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Seoul')))
    updated_at = db.Column(db.TIMESTAMP, nullable=False, default=lambda: datetime.now(pytz.timezone('Asia/Seoul')))
    last_login = db.Column(db.TIMESTAMP, nullable=True)

    def __repr__(self):
        return f"<User {self.email}>"
