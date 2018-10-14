from logging import getLogger
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from marshmallow import ValidationError
from auth_server.config import url_prefix
from auth_server.models.auth_model import Users, Roles, Resources, user_roles, resource_roles
from auth_server.models.errors import DoesNotExist
from auth_server.serializers.identity_serializers import UserSerializer, RoleSerializer, ResourceSerializer
from auth_server.utils.jwt import access_required
from auth_server.utils.view_utils import json_or_400
from auth_server.views.base_views import BasicCrudView, ManyManySubResource

identity_bp = Blueprint('identity', __name__)


class UsersView(BasicCrudView):
    resource_names = [
        url_prefix[1:] + ':users:r',
        url_prefix[1:] + ':users:w'
    ]
    decorators = [access_required(resource_names)]

    model = Users
    serializer = UserSerializer


class RolesView(BasicCrudView):
    resource_names = [
        url_prefix[1:] + ':roles:r',
        url_prefix[1:] + ':roles:w'
    ]
    decorators = [access_required(resource_names)]

    model = Roles
    serializer = RoleSerializer


class ResourcesView(BasicCrudView):
    resource_names = [
        url_prefix[1:] + ':resources:r',
        url_prefix[1:] + ':resources:w'
    ]
    decorators = [access_required(resource_names)]

    model = Resources
    serializer = ResourceSerializer


class UserRolesView(ManyManySubResource):
    resource_names = [
        url_prefix[1:] + ':users:r',
        url_prefix[1:] + ':users:w',
        url_prefix[1:] + ':roles:r',
    ]
    decorators = [access_required(resource_names)]

    base_model = Users
    relation_table = user_roles
    relation_field_to_base = 'user_id'
    relation_field_to_sub = 'role_id'
    sub_model = Roles
    fields = ['id', 'name', 'description']

    serializer = RoleSerializer


class RoleUsersView(ManyManySubResource):
    resource_names = [
        url_prefix[1:] + ':roles:r',
        url_prefix[1:] + ':users:w',
        url_prefix[1:] + ':users:r',
    ]
    decorators = [access_required(resource_names)]

    base_model = Roles
    relation_table = user_roles
    relation_field_to_base = 'role_id'
    relation_field_to_sub = 'user_id'
    sub_model = Users
    fields = ['id', 'username']

    serializer = UserSerializer


class RoleResourcesView(ManyManySubResource):
    resource_names = [
        url_prefix[1:] + ':roles:r',
        url_prefix[1:] + ':roles:w',
        url_prefix[1:] + ':resources:r',
    ]
    decorators = [access_required(resource_names)]

    base_model = Roles
    relation_table = resource_roles
    relation_field_to_base = 'role_id'
    relation_field_to_sub = 'resource_id'
    sub_model = Resources
    fields = ['id', 'path']

    serializer = ResourceSerializer


class ResourceRolesView(ManyManySubResource):
    resource_names = [
        url_prefix[1:] + ':resources:r',
        url_prefix[1:] + ':resources:w',
        url_prefix[1:] + ':roles:r',
    ]
    decorators = [access_required(resource_names)]

    base_model = Resources
    relation_table = resource_roles
    relation_field_to_base = 'resource_id'
    relation_field_to_sub = 'role_id'
    sub_model = Roles
    fields = ['id', 'name', 'description']

    serializer = ResourceSerializer


@identity_bp.route('/user_info', methods=['GET'])
@jwt_required
def get_user_info():
    id = get_jwt_identity()
    try:
        return UserSerializer().dumps(Users.get_info_by_id(id)), 200
    except DoesNotExist:
        return "resource does not exists anymore", 404


@identity_bp.route('/user_info', methods=['PATCH'])
@jwt_required
@json_or_400
def update_user_info():
    id = get_jwt_identity()
    try:
        in_data = UserSerializer(partial=True).load(request.get_json())
    except ValidationError as e:
        getLogger().exception(e)
        getLogger().error("validation error for update_user_info request: {}".format(e))
        return "bad format input for fields: {}".format(e.field_names), 422
    else:
        count = Users.update(**in_data).where(Users.id == id).execute()
        if count < 1:
            return "resource does not exists anymore", 404
        else:
            return "", 204
