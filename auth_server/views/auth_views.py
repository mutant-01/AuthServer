from logging import getLogger
from flask import Blueprint, request
from flask_jwt_extended import create_access_token
from marshmallow import ValidationError
from auth_server.serializers.auth_serializers import TokenInput, TokenOutput
from auth_server.user_manager.local_user_manager import LocalUserManager
from auth_server.utils.blacklist import UserBlackList
from auth_server.utils.view_utils import json_or_400

auth_bp = Blueprint('auth', __name__)

user_manger_class = LocalUserManager
user_blacklist_class = UserBlackList


@auth_bp.route('/token', methods=['post'])
@json_or_400
def token():
    input_schema = TokenInput()
    output_schema = TokenOutput()
    try:
        user = input_schema.load(request.get_json())
    except ValidationError as e:
        getLogger().info("Validation error for user login: {}, detail: {}".format(request.get_json(), e.messages))
        return "Validation error, the input data is invalid", 400
    else:
        user_manager = user_manger_class(user["username"], password=user["password"])
        user_from_db = user_manager.authenticate()
        if user_from_db is None:
            getLogger().info(
                "user {} failed to authenticate".format(user["username"])
            )
            return "authentication failed, no such username or password", 401
        # user_from_db is a python dictionary object that has 'username' and 'access' keys
        access_token = create_access_token(identity=user_from_db)
        return output_schema.dumps({"token": access_token}), 200
