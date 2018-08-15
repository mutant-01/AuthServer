from peewee import CharField, ForeignKeyField, TextField, CompositeKey
from auth_server import db_wrapper


class Users(db_wrapper.Model):
    class Meta:
        table_name = 'users'

    username = CharField(max_length=128, null=False, index=True, unique=True)  # todo it should be a hash index
    password = CharField(max_length=256, null=False)
    display_name = CharField(max_length=128, null=True)  # todo create another table for profile info
    avatar = TextField(null=True)


class Roles(db_wrapper.Model):
    class Meta:
        table_name = 'roles'

    name = CharField(max_length=256, null=False, unique=True)
    description = TextField(null=True)


class UserRoles(db_wrapper.Model):
    class Meta:
        table_name = 'user_roles'
        primary_key = CompositeKey('user_id', 'role_id')

    user_id = ForeignKeyField(Users, null=False, on_delete='CASCADE')
    role_id = ForeignKeyField(Roles, null=False, on_delete='CASCADE')


class Resources(db_wrapper.Model):
    class Meta:
        table_name = 'resources'

    path = CharField(max_length=1024, null=False, index=True)  # todo it should be a hash index


class ResourceRoles(db_wrapper.Model):
    class Meta:
        table_name = 'resource_roles'
        primary_key = CompositeKey('resource_id', 'role_id')

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


def get_all_many_many_as_sub(base_table, sub_table, relation_table, key_to_base, key_to_sub, base_id, fields):
    """"""
    results = db_wrapper.database.execute_sql(
        "select {sub}.* from {base} "
        "inner join {relation} on ({base}.id={relation}.{key_base}) "
        "inner join {sub} on ({sub}.id={relation}.{key_sub}) WHERE {relation}.{key_base}={base_id}".format(
            base=base_table,
            sub=sub_table,
            relation=relation_table,
            key_base=key_to_base,
            key_sub=key_to_sub,
            base_id=base_id
        )
    ).fetchall()
    if results is None:
        return []
    return [{k: v for k, v in zip(fields, result)} for result in results]


def get_one_many_many_as_sub(base_table, sub_table, relation_table, key_to_base, key_to_sub, base_id, sub_id, fields):
    """"""
    result = db_wrapper.database.execute_sql(
        "select {sub}.* from {base} "
        "inner join {relation} on ({base}.id={relation}.{key_base}) "
        "inner join {sub} on ({sub}.id={relation}.{key_sub}) "
        "WHERE {relation}.{key_base}={base_id} AND {relation}.{key_sub}={sub_id}".format(
            base=base_table,
            sub=sub_table,
            relation=relation_table,
            key_base=key_to_base,
            key_sub=key_to_sub,
            base_id=base_id,
            sub_id=sub_id
        )
    ).fetchone()
    if result is None:
        return {}
    return {k: v for k, v in zip(fields, result)}


def get_user_resources_by_roles(roles: list):
    if len(roles) < 1:
        raise TypeError("empty roles list")
    results = db_wrapper.database.execute_sql(
        "select  distinct(resources.path) from resource_roles "
        "inner join resources on (resource_roles.resource_id=resources.id) "
        "where resource_roles.role_id in ({roles});".format(
            roles=",".join(map(str, roles))
        )
    ).fetchall()
    return [r[0] for r in results]
