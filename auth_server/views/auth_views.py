from logging import getLogger
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_raw_jwt, get_jwt_claims
from flask_jwt_extended.config import config
from flask_jwt_extended.exceptions import JWTDecodeError, UserClaimsVerificationError
from flask_jwt_extended.tokens import decode_jwt
from flask_jwt_extended.utils import verify_token_claims
from marshmallow import ValidationError
from auth_server.models.auth_model import get_user_resources_by_roles
from auth_server.serializers.auth_serializers import TokenInput, TokenOutput, AuthorizeInput, AuthorizeOutput
from auth_server.serializers.identity_serializers import ResourceSerializer
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


@auth_bp.route('/revoke', methods=['POST'])
@jwt_required
def revoke():
    blacklist = user_blacklist_class()
    blacklist.persist_token_in_blacklist(get_raw_jwt()['jti'])
    return "", 204


@auth_bp.route('/authorize', methods=['POST'])  # todo only allow services block others in the gateway or use ssl mutual
@json_or_400
def authorize():
    """Authorizes token if its valid and not expired and has access to provided resources"""
    input_schema = AuthorizeInput()
    output_schema = AuthorizeOutput()
    try:
        in_data = input_schema.load(request.get_json())
    except ValidationError as e:
        getLogger().exception(e)
        getLogger().error("validation error for authorize request: {}".format(e))
        return "bad format input for fields: {}".format(e.field_names), 422

    try:
        jwt_data = decode_jwt(
            encoded_token=in_data["token"],
            secret=config.decode_key,
            algorithm=config.algorithm,
            identity_claim_key=config.identity_claim_key,
            user_claims_key=config.user_claims_key
        )
    except JWTDecodeError as e:
        getLogger().exception(e)
        getLogger().error("jwt cannot be decoded: {}".format(in_data["token"]))
        return "jwt cannot be decoded", 422
    else:
        try:
            verify_token_claims(jwt_data)
        except UserClaimsVerificationError as e:
            getLogger().exception(e)
            getLogger().error("jwt claims verification failed: {}".format(in_data["token"]))
            return "jwt claims verification failed", 422

        # check if token in revoked blacklist
        blacklist = user_blacklist_class()
        if blacklist.token_in_blacklist(jwt_data["jti"]):
            getLogger().info(" authorize: token in revoke black list: {}".format(in_data))
            return "token in black list", 401

        try:
            roles = jwt_data["user_claims"]["roles"]
        except KeyError as e:
            getLogger().exception(e)
            getLogger().error("cannot access jwt claims: {}".format(in_data))
            return "bad format claims", 422
        else:
            resources = user_manger_class.authorize(roles=roles, resources=in_data["resources"])
            return output_schema.dumps({"token": in_data["token"], "resources": resources}), 200


@auth_bp.route('/user_resources', methods=['GET'])
@jwt_required
def get_user_resources():
    claims = get_jwt_claims()
    try:
        roles = claims["roles"]
    except KeyError as e:
        getLogger().exception(e)
        getLogger().error("no roles in claims")
        return "invalid token", 401
    else:
        try:
            return ResourceSerializer(exclude=("id", )).dumps(get_user_resources_by_roles(roles), many=True), 200
        except TypeError as e:
            getLogger().exception(e)
            getLogger().error("token '{}' have no roles so have no allowed resources".format(get_raw_jwt()))
            return jsonify([]), 200
