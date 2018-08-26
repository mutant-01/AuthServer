import argparse
from auth_server import create_app, db_wrapper
from auth_server.models.auth_model import Users, Roles, UserRoles, Resources, ResourceRoles
from auth_server.utils.password import hash_password
from auth_server.views.identity_views import (
    UsersView, ResourcesView, RolesView
)


def parse_input():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument(
        "--username", required=True, type=str, help="The admin user to access roles, resources and users"
    )
    arg_parser.add_argument(
        "--password", required=True, type=str, help="The admin password"
    )
    return vars(arg_parser.parse_args())


if __name__ == '__main__':
    app = create_app({})
    db_wrapper.database.create_tables([Users, Roles, UserRoles, Resources, ResourceRoles])

    in_data = parse_input()

    # create admin user
    admin_user, created = Users.get_or_create(username=in_data['username'], password=hash_password(in_data['password']))
    if not created:
        print("The username provided already exists")

    # create admin role
    admin_role, created = Roles.get_or_create(name="admin", description="Has access to all identity management endpoints")
    if not created:
        print("The admin role already exists")

    _, created = UserRoles.get_or_create(role_id=admin_role.id, user_id=admin_user.id)
    if not created:
        print("The UserRoles for admin user already exists")

    # create resources
    for view in [
        UsersView, ResourcesView, RolesView
    ]:
        for resource_name in view.resource_names:
            r, created = Resources.get_or_create(path=resource_name)
            if not created:
                print("The '{}' resource already exists".format(resource_name))

            _, created = ResourceRoles.get_or_create(role_id=admin_role.id, resource_id=r.id)
            if not created:
                print("The ResourceRole for '{},{}' already exists".format(r.id, admin_role.id))
