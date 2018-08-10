from flask_jwt_extended import jwt_required
from auth_server.models.auth_model import Users
from auth_server.serializers.identity_serializers import UserSerializer
from auth_server.views.base_views import BasicCrudView


class UsersView(BasicCrudView):
    decorators = [jwt_required]

    model = Users
    serializer = UserSerializer
