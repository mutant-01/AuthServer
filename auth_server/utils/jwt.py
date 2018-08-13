from functools import wraps
from logging import getLogger
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_claims, get_raw_jwt
from auth_server import jwt
from datetime import datetime
from auth_server.serializers.auth_serializers import Claims
from auth_server.user_manager.local_user_manager import LocalUserManager
from auth_server.utils.blacklist import UserBlackList


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


@jwt.token_in_blacklist_loader
def check_if_token_in_blacklist(decrypted_token):
    jti = decrypted_token['jti']
    blacklist = UserBlackList()
    return blacklist.token_in_blacklist(jti)


def access_required(resources: list):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt_claims()
            result = LocalUserManager.authorize(claims.get("roles", []), resources)
            if False in result.values():
                getLogger().info("access denied token: '{}'  resources/permissions: '{}'".format(get_raw_jwt(), result))
                return "Access denied", 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator
