"""=========================================================================================
<profile.py>

이 모듈은 사용자 프로필 관련 API 엔드포인트를 관리합니다. 사용자 프로필 조회, 프로필 정보 업데이트,
프로필 사진 변경과 같은 기능을 제공합니다.

주요 기능:
- 사용자 프로필 조회: 로그인된 사용자의 프로필 정보를 조회합니다.
- 프로필 정보 업데이트: 사용자가 자신의 이름, 닉네임, 이메일 등의 정보를 업데이트할 수 있습니다.
- 프로필 사진 변경: 사용자가 자신의 프로필 사진을 업로드하거나 변경할 수 있습니다.

이 모듈은 Flask와 SQLAlchemy를 사용하여 구현되었으며, 사용자 데이터의 관리 및 업데이트를 처리합니다.

========================================================================================="""

# import libraries
from app import bcrypt, db
from app.models.user import Users
from flask import Blueprint, request, jsonify
import flask_jwt_extended
import re
import pytz
from datetime import datetime