"""=========================================================================================
<auth.py>

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
from app import bcrypt, db
from app.utils.exceptions import *
from app.utils.decorators import *
from app.models.user import Users
# import flask modules
from flask import Blueprint, request, jsonify
import flask_jwt_extended
# import else
import re
import pytz
from datetime import datetime

auth_routes = Blueprint("auth", __name__)

# END (2024.05.20.)
@auth_routes.route("/login", methods=["POST"])
@error_handler()
def login():
    """User login function.
    
    Params:
        email `str`:
            User's email.
        password `str`:
            User's password.
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        access_token `str`:
            JWT access token.
        refresh_token `str`:
            JWT refresh token.
    """
    validate_json()
    validate_json_params("email", "password")

    email = request.json["email"]
    password = request.json["password"]

    # Query the database for the user
    user = Users.query.filter_by(email=email).first()
    if user is None:
        raise UserNotExistException

    # Check the password
    if bcrypt.check_password_hash(user.password, password):
        # Update last login
        # Get current time in Korea timezone
        last_login = datetime.now(pytz.timezone("Asia/Seoul"))
        user.last_login = last_login
        db.session.commit()

        # Set the access and refresh tokens
        access_token = flask_jwt_extended.create_access_token(identity=email)
        refresh_token = flask_jwt_extended.create_refresh_token(identity=email)

        return jsonify({
            "result": "success",
            "msg": "login",
            "err_code": "00",
            "access_token": access_token,
            "refresh_token": refresh_token
        }), 200
    else:
        raise IncorrectPasswordException

# END (2024.05.16.)
@auth_routes.route("/dup_check", methods=["POST"])
def dup_check():
    """
    Check for duplicate email or nickname during user registration.

    Params:
        email `str`:
            User's email.
        nickname `str`:
            User's nickname.
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
    """
    # Error: Data format is not JSON
    if not request.is_json:
        return jsonify({
            "result":"error", 
            "msg":"missing json in request",
            "err_code":"10"
        }), 400
    
    email = request.json.get("email")
    nickname = request.json.get("nickname")
    
    if not email and not nickname:
        return jsonify({
            "result": "error", 
            "msg": f"missing email or nickname parameter", 
            "err_code": "11"
        }), 400

    # Check for duplicate email
    if email and Users.query.filter_by(email=email).first():
        return jsonify({
            "result": "error",
            "msg": "user already exists with this email",
            "err_code": "21"
        }), 409
    
    # Check for duplicate nickname
    if nickname and Users.query.filter_by(nickname=nickname).first():
        return jsonify({
            "result": "error",
            "msg": "duplicate nickname",
            "err_code": "23"
        }), 409
    
    return jsonify({
        "result": "success",
        "msg": "no duplicate values found",
        "err_code": "00"
    }), 200

# END (2024.05.20.)
@auth_routes.route("/register", methods=["POST"])
def register():
    """
    Register a new user.

    Params:
        name `str`:
            User's name.
        nickname `str`:
            User's nickname. Nickname must be unique.
        email `str`:
            User's email. Email must be unique.
        password `str`: 
            User's password. 
        phone `str`:
            User's phone number. 
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
    """
    # Error: Data format is not JSON
    if not request.is_json:
        return jsonify({
            "result":"error", 
            "msg":"missing json in request",
            "err_code":"10"
        }), 400
    
    # Error: Required parameter is empty or missing
    required_fields = ["name", "nickname", "email", "password"]
    for field in required_fields:
        if field not in request.json or not request.json[field]:
            return jsonify({
                "result": "error", 
                "msg": f"missing {field} parameter", 
                "err_code": "11"
            }), 400

    name = request.json["name"]
    nickname = request.json["nickname"]
    email = request.json["email"]
    password = request.json["password"]

    # Check for valid email format
    if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
        return jsonify({
            "result": "error", 
            "msg": "invalid email format", 
            "err_code": "12"
        }), 400

    # Check for valid name and nickname format
    if not re.match(r"^[ㄱ-ㅎ|가-힣|a-zA-Z0-9]{1,8}$", nickname):
        return jsonify({
            "result": "error", 
            "msg": "invalid nickname format or length", 
            "err_code": "13"
        }), 400
    
    # Check for valid password format
    if not re.match(r"^(?=.*[a-zA-Z])(?=.*[!@#$%^*+=-])(?=.*[0-9]).{10,25}$", password):
        return jsonify({
            "result": "error", 
            "msg": "invalid password format or length", 
            "err_code": "14"
        }), 400


    # Check for existing email or nickname
    if Users.query.filter_by(email=email).first():
        return jsonify({
            "result": "error", 
            "msg": "user already exists with this email", 
            "err_code": "21"
        }), 409
    if Users.query.filter_by(nickname=nickname).first():
        return jsonify({
            "result": "error", 
            "msg": "duplicate nickname", 
            "err_code": "23"
        }), 409
    
    # Hash password
    hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

    # Create a new User instance
    new_user = Users(
        email=email,
        password=hashed_password,
        name=name,
        nickname=nickname
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({
        "result":"success", 
        "msg":"registration successful", 
        "err_code":"00"
    }), 200

# END (2024.05.16.)
@auth_routes.route("/protected", methods=["GET"])
@flask_jwt_extended.jwt_required()
def protected():
    """
    User Authenrication Function
    
    Returns:
        result `str`:
            Response success or error status ("success" or "error").
        msg `str`:
            Response message.
        err_code `str`:
            Error code (refer to API_GUIDE.md)
        email `str`:
            User's email
        user `str`:
            User's nickname
        name `str`:
            User's name
    """
    curr_user_email = flask_jwt_extended.get_jwt_identity()

    user = Users.query.filter_by(email=curr_user_email).first()

    # If user not exist
    if not user:
        return jsonify({
            "result": "error",
            "msg": "user does not exist",
            "err_code": "20"
        }), 422
    else:
        return jsonify({
            "result": "success",
            "msg": "user authentication",
            "err_code": "00",
            "email": user.email,
            "user": user.nickname,
            "name": user.name
        }), 200


'''
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
'''
