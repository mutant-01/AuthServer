from peewee import CharField, ForeignKeyField, DateTimeField, TextField
from auth_server import db_wrapper


class Users(db_wrapper.Model):
    class Meta:
        table_name = 'users'

    username = CharField(max_length=128, null=False, index=True, unique=True)  # todo it should be a hash index
    password = CharField(max_length=256, null=False)


class Roles(db_wrapper.Model):
    class Meta:
        table_name = 'roles'

    name = CharField(max_length=256, null=False, unique=True)
    description = TextField(null=True)


class UserRoles(db_wrapper.Model):
    class Meta:
        table_name = 'user_roles'

    user_id = ForeignKeyField(Users, null=False, on_delete='CASCADE')
    role_id = ForeignKeyField(Roles, null=False, on_delete='CASCADE')


class Resources(db_wrapper.Model):
    class Meta:
        table_name = 'resources'

    path = CharField(max_length=1024, null=False, index=True)  # todo it should be a hash index


class ResourceRoles(db_wrapper.Model):
    class Meta:
        table_name = 'resource_roles'
    resource_id = ForeignKeyField(Resources, null=False, on_delete='CASCADE')
    role_id = ForeignKeyField(Roles, null=False, on_delete='CASCADE')


def get_user_by_user_pass(username, password):
    tuple_result = db_wrapper.database.execute_sql(
        "SELECT users.id, array_agg(user_roles.role_id) "
        "FROM users LEFT JOIN user_roles ON (users.id = user_roles.user_id) "
        "where users.username='{username}' AND users.password='{password}'"
        "group by users.id".format(
            username=username, password=password
        )
    ).fetchone()
    if tuple_result is None:
        return tuple_result
    return {"id": tuple_result[0], "roles": tuple_result[1]}


def get_resources_by_roles(roles: set, resources: set) -> list:
    """

    :return: resources allowed by provided roles
    :raises TypeError: if either of roles or resources is empty.
    """
    if len(roles) < 1:
        raise TypeError("empty roles")
    if len(resources) < 1:
        raise TypeError("empty resources")
    result = db_wrapper.database.execute_sql(
        "SELECT array_agg(resources.path) "
        "FROM resource_roles INNER JOIN resources ON (resource_roles.resource_id=resources.id) "
        "WHERE resources.path IN ({resources}) AND role_id IN ({roles})".format(
            resources="'" + "','".join(resources) + "'",
            roles=','.join(map(str, roles))
        )
    ).fetchone()
    if result[0] is None:
        return []
    return result[0]
