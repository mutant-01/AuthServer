from flask_admin import expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from auth_server import db_wrapper
from auth_server.config import url_prefix
from auth_server.models.auth_model import Users, Resources, Roles, get_resources_by_user_pass
from flask import request, Response
from auth_server.utils.password import hash_password


class RestrictedModelView:
    resources = {
        url_prefix[1:] + ':users:r',
        url_prefix[1:] + ':users:w',
        url_prefix[1:] + ':roles:r',
        url_prefix[1:] + ':roles:w',
        url_prefix[1:] + ':resources:r',
        url_prefix[1:] + ':resources:w'
    }

    def is_accessible(self):
        if request.authorization:
            accessible_resources = get_resources_by_user_pass(
                request.authorization.username, hash_password(request.authorization.password))
            return self.resources in accessible_resources or self.resources == accessible_resources
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})


class IndexView(AdminIndexView, RestrictedModelView):

    def is_accessible(self):
        if request.authorization:
            accessible_resources = get_resources_by_user_pass(
                request.authorization.username, hash_password(request.authorization.password))
            return self.resources in accessible_resources or self.resources == accessible_resources
        else:
            return False

    def inaccessible_callback(self, name, **kwargs):
        return Response(
            'Could not verify your access level for that URL.\n'
            'You have to login with proper credentials', 401,
            {'WWW-Authenticate': 'Basic realm="Login Required"'})

    @expose('/')
    def index(self):
        return super().index()


class UserModelView(RestrictedModelView, ModelView):

    page_size = 50
    column_exclude_list = ['password', ]
    column_searchable_list = ['username', 'display_name', 'service_name']
    column_hide_backrefs = False
    column_list = ['username', 'display_name', 'service_name', 'roles']


class RoleModelView(RestrictedModelView, ModelView):
    page_size = 50
    column_searchable_list = ['name']
    column_hide_backrefs = False
    column_list = ['name', 'description', 'users', 'resources']


class ResourceModelView(RestrictedModelView, ModelView):
    page_size = 50
    column_searchable_list = ['path']
    column_hide_backrefs = False
    column_list = ['path', 'description', 'roles']


def register():
    from auth_server import admin
    admin.add_view(UserModelView(Users, db_wrapper.session))
    admin.add_view(RoleModelView(Roles, db_wrapper.session))
    admin.add_view(ResourceModelView(Resources, db_wrapper.session))
