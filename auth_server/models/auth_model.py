from logging import getLogger
from sqlalchemy import Integer, ForeignKey, and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import relationship
from sqlalchemy.sql import select
from auth_server import db_wrapper
from auth_server.models.errors import DoesNotExist, ConstraintViolation
from auth_server.models.utils import CrudModel

user_roles = db_wrapper.Table(
    'user_roles',
    db_wrapper.metadata,
    db_wrapper.Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    db_wrapper.Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

resource_roles = db_wrapper.Table(
    'resource_roles',
    db_wrapper.metadata,
    db_wrapper.Column('resource_id', Integer, ForeignKey('resources.id', ondelete="CASCADE"), primary_key=True),
    db_wrapper.Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)


class Users(db_wrapper.Model, CrudModel):
    __tablename__ = 'users'

    id = db_wrapper.Column(db_wrapper.Integer, primary_key=True)
    username = db_wrapper.Column(db_wrapper.String(128), unique=True, nullable=False)
    password = db_wrapper.Column(db_wrapper.String(256), nullable=False)
    display_name = db_wrapper.Column(db_wrapper.String(128), nullable=True)
    avatar = db_wrapper.Column(db_wrapper.Text, nullable=True)
    service_name = db_wrapper.Column(db_wrapper.String(128), nullable=True)
    roles = relationship(
        "Roles",
        secondary="user_roles",
        back_populates="users",
    )

    def __str__(self):
        return "user '{}', with id {}".format(self.username, self.id)

    @classmethod
    def get_info_by_id(cls, id):
        user = db_wrapper.session.execute(
            select([cls.username, cls.display_name, cls.avatar]).where(cls.id == id)
        ).first()
        db_wrapper.session.commit()
        if user is None:
            getLogger().error("user id '{}' does not exists")
            raise DoesNotExist
        return dict(user)


username_hash_index = db_wrapper.Index("username_hash_index", Users.username, postgresql_using='hash')


class Roles(db_wrapper.Model, CrudModel):
    __tablename__ = 'roles'

    id = db_wrapper.Column(db_wrapper.Integer, primary_key=True)
    name = db_wrapper.Column(db_wrapper.String(256), nullable=False, unique=True)
    description = db_wrapper.Column(db_wrapper.Text, nullable=True)
    users = relationship(
        "Users",
        secondary="user_roles",
        back_populates="roles"
    )
    resources = relationship(
        "Resources",
        secondary="resource_roles",
        back_populates="roles"
    )

    def __str__(self):
        return "role '{}', with id {}, description: '{}'".format(self.name, self.id, self.description)


role_name_hash_index = db_wrapper.Index("role_name_hash_index", Roles.name, postgresql_using='hash')


class Resources(db_wrapper.Model, CrudModel):
    __tablename__ = 'resources'

    id = db_wrapper.Column(db_wrapper.Integer, primary_key=True)
    path = db_wrapper.Column(db_wrapper.String(1024), nullable=False, unique=True)
    description = db_wrapper.Column(db_wrapper.Text, nullable=True)
    value = db_wrapper.Column(db_wrapper.String(1024), nullable=True)
    roles = relationship(
        "Roles",
        secondary="resource_roles",
        back_populates="resources"
    )

    def __str__(self):
        return "resource '{}', with id {}".format(self.path, self.id)


resource_path_hash_index = db_wrapper.Index("resource_path_hash_index", Resources.path, postgresql_using='hash')


def get_user_by_user_pass(username, password):
    tuple_result = db_wrapper.session.execute(
        "SELECT users.id, array_agg(user_roles.role_id) "
        "FROM users LEFT JOIN user_roles ON (users.id = user_roles.user_id) "
        "where users.username='{username}' AND users.password='{password}'"
        "group by users.id".format(
            username=username, password=password
        )
    ).first()
    db_wrapper.session.commit()
    if tuple_result is None:
        return tuple_result
    return {"id": tuple_result[0], "roles": tuple_result[1]}


def get_resources_by_roles(roles: set, resources: set) -> list:
    """

    :return: resources and their values allowed by provided roles
    :raises TypeError: if either of roles or resources is empty.
    """
    if len(roles) < 1:
        raise TypeError("empty roles")
    if len(resources) < 1:
        raise TypeError("empty resources")
    result = db_wrapper.session.execute(
        "SELECT DISTINCT resources.path, resources.value "
        "FROM resource_roles INNER JOIN resources ON (resource_roles.resource_id=resources.id) "
        "WHERE resources.path IN ({resources}) AND role_id IN ({roles})".format(
            resources="'" + "','".join(resources) + "'",
            roles=','.join(map(str, roles))
        )
    ).fetchall()
    db_wrapper.session.commit()
    return list(result)


def get_all_many_many_as_sub(
        base_model: db_wrapper.Model,
        sub_model: db_wrapper.Model,
        relation_table: db_wrapper.Table,
        relation_field_to_base: str,
        relation_field_to_sub: str,
        base_id: str, fields: list):
    """Returns all instances of sub model connected to the base model via many-many relation.
    :param base_model: The source model of the many to many relationship.
    :param sub_model: the target model of the many to many relationship.
    :param relation_table: the table(sqlalchemy relation table) represinting the many to many relationship.
    :param relation_field_to_base: the foreign key from the relation table to the source(base) table.
    :param relation_field_to_sub: the foreign key from the relation table to the target(sub) table.
    :param base_id: the id of the base model instance.
    :param fields: list of field names of the target model to be fetched
    :return: instances of the sub model that has relationship with the source model instance.
    """
    results = db_wrapper.session.execute(
        "select {fields} from {base} "
        "inner join {relation} on ({base}.id={relation}.{field_to_base}) "
        "inner join {sub} on ({sub}.id={relation}.{field_to_sub}) WHERE {relation}.{field_to_base}={base_id}".format(
            fields=sub_model.__table__.name + "." + ", {}.".format(sub_model.__table__.name).join(fields),
            base=base_model.__table__.name,
            sub=sub_model.__table__.name,
            relation=relation_table.name,
            field_to_base=relation_field_to_base,
            field_to_sub=relation_field_to_sub,
            base_id=base_id
        )
    )
    db_wrapper.session.commit()
    if results is None:
        return []
    return [sub_model(**dict(r)) for r in results]


def get_one_many_many_as_sub(
        base_model: db_wrapper.Model,
        sub_model: db_wrapper.Model,
        relation_table: db_wrapper.Table,
        relation_field_to_base: str,
        relation_field_to_sub: str,
        base_id, sub_id, fields):
    """Returns an instance of sub model connected to the base model via many-many relation by the provided id.

    :param base_model: The source model of the many to many relationship.
    :param sub_model: the target model of the many to many relationship.
    :param relation_table: the table(sqlalchemy relation table) represinting the many to many relationship.
    :param relation_field_to_base: the foreign key from the relation table to the source(base) table.
    :param relation_field_to_sub: the foreign key from the relation table to the target(sub) table.
    :param base_id: the id of the base model instance.
    :param fields: list of field names of the target model to be fetched
    :param sub_id: the id of the sub model instance to be returned.
    :return: instance of the sub model that has relationship with the source model instance and match the provided id.
    """
    result = db_wrapper.session.execute(
        "select {fields} from {base} "
        "inner join {relation} on ({base}.id={relation}.{field_to_base}) "
        "inner join {sub} on ({sub}.id={relation}.{field_to_sub}) "
        "WHERE {relation}.{field_to_base}={base_id} AND {relation}.{field_to_sub}={sub_id}".format(
            fields=sub_model.__table__.name + "." + ", {}.".format(sub_model.__table__.name).join(fields),
            base=base_model.__table__.name,
            sub=sub_model.__table__.name,
            relation=relation_table.name,
            field_to_base=relation_field_to_base,
            field_to_sub=relation_field_to_sub,
            base_id=base_id,
            sub_id=sub_id
        )
    ).first()
    db_wrapper.session.commit()
    if result is None:
        return {}
    return sub_model(**result)


def get_user_resources_by_roles(roles: list):
    if len(roles) < 1:
        raise TypeError("empty roles list")
    results = db_wrapper.session.execute(
        "select  distinct(resources.path), resources.description from resource_roles "
        "inner join resources on (resource_roles.resource_id=resources.id) "
        "where resource_roles.role_id in ({roles});".format(
            roles=",".join(map(str, roles))
        )
    ).fetchall()
    db_wrapper.session.commit()
    return [Resources(**r) for r in results]


def insert_to_table(table: db_wrapper.Table, data: dict):
    """insert the provided data into the provided Table object

    :raises IntegrityError: in case of constraint violation.
    """
    try:
        db_wrapper.session.execute(table.insert(), data)
    except IntegrityError as e:
        getLogger().error("insert into table {} failed, data: {}".format(table.name, data))
        getLogger().exception(e)
        db_wrapper.session.rollback()
        raise ConstraintViolation
    db_wrapper.session.commit()


def delete_from_relation_table(
        table: db_wrapper.Table, base_id_field: str, sub_id_field: str, base_id: str, sub_id: str
):
    """delete a row from the table according to the provided id

    :param table: the table object the operation will be applied to.
    :param match_data: dictionary containing the criteria of the query in form of {"field1": "value", "field2": "value"}
    :returns bool: True if criteria matched, False otherwise.
    """
    r = db_wrapper.session.execute(table.delete().where(
        and_(getattr(table.c, base_id_field) == base_id, getattr(table.c, sub_id_field) == sub_id)
    ))
    db_wrapper.session.commit()
    if r.rowcount > 0:
        return True
    else:
        return False


def get_resources_by_user_pass(username: str, password: str):
    """

    :param username: the username in query criteria.
    :param password: the password in query criteria.
    :return: set of Resource paths the user has access to.
    """
    results = db_wrapper.session.execute(
        "select resources.path from users inner join user_roles on (users.id=user_roles.user_id) " 
        "inner join resource_roles on (user_roles.role_id=resource_roles.role_id) " 
        "inner join resources on (resources.id=resource_roles.resource_id) "
        "where users.username='{username}' and password='{password}'".format(username=username, password=password)
    )
    db_wrapper.session.commit()
    if not results:
        return []
    return {r[0] for r in results}
