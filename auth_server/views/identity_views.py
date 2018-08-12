from flask_jwt_extended import jwt_required
from auth_server.models.auth_model import Users, Roles, Resources, UserRoles, ResourceRoles
from auth_server.serializers.identity_serializers import UserSerializer, RoleSerializer, ResourceSerializer
from auth_server.views.base_views import BasicCrudView, ManyManySubResource


class UsersView(BasicCrudView):
    decorators = [jwt_required]

    model = Users
    serializer = UserSerializer


class RolesView(BasicCrudView):
    decorators = [jwt_required]

    model = Roles
    serializer = RoleSerializer


class ResourcesView(BasicCrudView):
    decorators = [jwt_required]

    model = Resources
    serializer = ResourceSerializer


class UserRolesView(ManyManySubResource):
    base_table = 'users'
    relation_table = 'user_roles'
    relation_model = UserRoles
    relation_key_to_base = 'user_id'
    relation_key_to_sub = 'role_id'
    sub_table = 'roles'
    fields = ['id', 'name', 'description']

    serializer = RoleSerializer


class RoleUsersView(ManyManySubResource):
    base_table = 'roles'
    relation_table = 'user_roles'
    relation_model = UserRoles
    relation_key_to_base = 'role_id'
    relation_key_to_sub = 'user_id'
    sub_table = 'users'
    fields = ['id', 'username']

    serializer = UserSerializer


class RoleResourcesView(ManyManySubResource):
    base_table = 'roles'
    relation_table = 'resource_roles'
    relation_model = ResourceRoles
    relation_key_to_base = 'role_id'
    relation_key_to_sub = 'resource_id'
    sub_table = 'resources'
    fields = ['id', 'path']

    serializer = ResourceSerializer
