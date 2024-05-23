from flask import Blueprint, jsonify

server_status_routes = Blueprint("server_status", __name__)

@server_status_routes.route("/", methods=["GET", "POST"])
def server_status():
    return jsonify({
        "result":"success", 
        "msg":"server is online",
        "err_code":"00"
    }), 200
