import argparse
from sqlalchemy.exc import ProgrammingError
from auth_server import create_app, db_wrapper
from auth_server.models.auth_model import (
    Users, username_hash_index, Roles, role_name_hash_index,
    resource_path_hash_index, Resources)
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
    with app.app_context():
        db_wrapper.create_all(app=app)
        for index in [username_hash_index, role_name_hash_index, resource_path_hash_index]:
            try:
                index.create(bind=db_wrapper.engine)
            except ProgrammingError as e:
                print("Error in index creation: {}".format(e))
        in_data = parse_input()

        # create admin user
        admin = Users(username=in_data["username"], password=hash_password(in_data['password']))
        db_wrapper.session.add(admin)

        # create admin role
        admin_role = Roles(name="admin", description="Has access to all identity management endpoints")
        db_wrapper.session.add(admin_role)
        admin.roles.append(admin_role)

        # create resources
        for view in [
            UsersView, ResourcesView, RolesView
        ]:
            for resource_name in view.resource_names:
                r = db_wrapper.session.query(Resources).filter_by(path=resource_name).first()
                if not r:
                    r = Resources(path=resource_name)
                r.roles.append(admin_role)
                db_wrapper.session.add(r)

        db_wrapper.session.commit()
