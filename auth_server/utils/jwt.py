from flask import jsonify
from auth_server import jwt
from datetime import datetime
from auth_server.serializers.auth_serializers import Claims


@jwt.user_claims_loader
def add_claims_to_access_token(user, *args, **kwargs):
    user["iss_dt"] = datetime.utcnow()
    return Claims().dump(user)


@jwt.user_identity_loader
def user_identity_lookup(user, *args, **kwargs):
    return user.get("id")


@jwt.invalid_token_loader
def invalid_token(e):
    return jsonify({
        'status': 401,
        'msg': 'The token is invalid'
    }), 401
