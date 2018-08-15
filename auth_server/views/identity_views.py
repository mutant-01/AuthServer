from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from peewee import DoesNotExist
from auth_server.config import url_prefix
from auth_server.models.auth_model import Users, Roles, Resources, UserRoles, ResourceRoles
from auth_server.serializers.identity_serializers import UserSerializer, RoleSerializer, ResourceSerializer
from auth_server.utils.jwt import access_required
from auth_server.views.base_views import BasicCrudView, ManyManySubResource

identity_bp = Blueprint('identity', __name__)


class UsersView(BasicCrudView):
    decorators = [access_required(['users-access'])]

    model = Users
    serializer = UserSerializer


class RolesView(BasicCrudView):
    decorators = [access_required(['roles-access'])]

    model = Roles
    serializer = RoleSerializer


class ResourcesView(BasicCrudView):
    decorators = [access_required(['resources-access'])]

    model = Resources
    serializer = ResourceSerializer


class UserRolesView(ManyManySubResource):
    decorators = [access_required(['users-access', 'roles-access'])]

    base_table = 'users'
    relation_table = 'user_roles'
    relation_model = UserRoles
    relation_key_to_base = 'user_id'
    relation_key_to_sub = 'role_id'
    sub_table = 'roles'
    fields = ['id', 'name', 'description']

    serializer = RoleSerializer


class RoleUsersView(ManyManySubResource):
    decorators = [access_required(['users-access', 'roles-access'])]

    base_table = 'roles'
    relation_table = 'user_roles'
    relation_model = UserRoles
    relation_key_to_base = 'role_id'
    relation_key_to_sub = 'user_id'
    sub_table = 'users'
    fields = ['id', 'username']

    serializer = UserSerializer


class RoleResourcesView(ManyManySubResource):
    decorators = [access_required(['roles-access', 'resources-access'])]

    base_table = 'roles'
    relation_table = 'resource_roles'
    relation_model = ResourceRoles
    relation_key_to_base = 'role_id'
    relation_key_to_sub = 'resource_id'
    sub_table = 'resources'
    fields = ['id', 'path']

    serializer = ResourceSerializer


class ResourceRolesView(ManyManySubResource):
    decorators = [access_required(['resources-access', 'roles-access'])]

    base_table = 'resources'
    relation_table = 'resource_roles'
    relation_model = ResourceRoles
    relation_key_to_base = 'resource_id'
    relation_key_to_sub = 'role_id'
    sub_table = 'roles'
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
