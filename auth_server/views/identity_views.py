from flask_jwt_extended import jwt_required
from auth_server.models.auth_model import Users, Roles
from auth_server.serializers.identity_serializers import UserSerializer, RoleSerializer
from auth_server.views.base_views import BasicCrudView


class UsersView(BasicCrudView):
    decorators = [jwt_required]

    model = Users
    serializer = UserSerializer


class RolesView(BasicCrudView):
    decorators = [jwt_required]

    model = Roles
    serializer = RoleSerializer
