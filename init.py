from auth_server import create_app, db_wrapper
from auth_server.models.auth_model import Users, Roles, UserRoles, Resources, ResourceRoles


app = create_app({})
db_wrapper.database.create_tables([Users, Roles, UserRoles, Resources, ResourceRoles])
