from flask_jwt_extended import jwt_required
from auth_server.models.auth_model import Users, Roles, Resources, UserRoles
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
