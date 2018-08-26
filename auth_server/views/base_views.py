from logging import getLogger
from flask import request
from flask.views import MethodView
from marshmallow import Schema, ValidationError
from peewee import DoesNotExist, IntegrityError
from auth_server import db_wrapper
from auth_server.models.auth_model import get_all_many_many_as_sub, get_one_many_many_as_sub
from auth_server.serializers.identity_serializers import IdSerializer


class BasicCrudView(MethodView):
    """The class is meant to be inherited"""

    # should be a Peewee model
    model = db_wrapper.Model

    # should be a Marshmallow schema
    serializer = Schema

    def get(self, id):
        """Returns all resources or one by id"""
        # returns all records of the model
        if id is None:
            return self.serializer().dumps(self.model.select(), many=True), 200
        # returns a record by id
        else:
            try:
                record = self.model.get_by_id(id)
            except DoesNotExist:
                return "Resource Does not exist", 404
            else:
                return self.serializer().dumps(record), 200

    def post(self):
        """creates new resource"""
        serializer_obj = self.serializer()
        json_data = request.get_json()
        if json_data is None:
            return "Invalid json", 400
        try:
            data = serializer_obj.load(json_data)
        except ValidationError as e:
            getLogger().exception(e)
            return "validation error for: {}".format(e.field_names), 422
        else:
            try:
                id = self.model.insert(**data).execute()
            except IntegrityError as e:
                getLogger().exception(e)
                return "Resource already exists", 409
            return serializer_obj.dumps({"id": id}), 201

    def patch(self, id):
        """update resource"""
        serializer_obj = self.serializer()
        json_data = request.get_json()
        if json_data is None:
            return "Invalid json", 400
        try:
            data = serializer_obj.load(request.get_json(), partial=True)
        except ValidationError as e:
            getLogger().exception(e)
            return "validation error for: {}".format(e.field_names), 422
        else:
            try:
                self.model.update(**data).where(self.model.id == id).execute()
            except IntegrityError as e:
                getLogger().exception(e)
                return "Resource already exists", 409
            return "", 204

    def delete(self, id):
        if self.model.delete().where(self.model.id == id).execute() > 0:
            return "", 204
        else:
            return "Resource Does not exist", 404


class ManyManySubResource(MethodView):
    """represent a many to many relation as sub resource.

    the relation must be assumed to have a direction from one of source tables"""
    #  todo tight dependency to db, replace peewee with some other ORM
    base_table = ''
    relation_table = ''
    relation_model = db_wrapper.Model
    relation_key_to_base = ''
    relation_key_to_sub = ''
    sub_table = ''
    fields = []

    # sub resource serializer
    serializer = Schema

    def get(self, base_id, id):
        """Returns all resources or one by id"""
        serializer_obj = self.serializer()
        # returns all records of the model
        if id is None:
            db_data = get_all_many_many_as_sub(
                self.base_table, self.sub_table, self.relation_table,
                self.relation_key_to_base, self.relation_key_to_sub, base_id, self.fields
            )
            return serializer_obj.dumps(db_data, many=True), 200
        # returns a record by id
        else:
            db_data = get_one_many_many_as_sub(
                self.base_table, self.sub_table, self.relation_table,
                self.relation_key_to_base, self.relation_key_to_sub, base_id, id, self.fields
            )
            if not db_data:
                return "Resource Does not exist", 404
            return serializer_obj.dumps(db_data), 200

    def post(self, base_id):
        """creates new resource"""
        serializer_obj = IdSerializer()
        json_data = request.get_json()
        if json_data is None:
            return "Invalid json", 400
        try:
            data = serializer_obj.load(json_data)
        except ValidationError as e:
            getLogger().exception(e)
            return "validation error for: {}".format(e.field_names), 422
        else:
            data[self.relation_key_to_base] = base_id
            data[self.relation_key_to_sub] = data.pop("id")
            try:
                self.relation_model.insert(**data).execute()
            except IntegrityError as e:
                getLogger().exception(e)
                return "Resource already exists or system constraint", 409
            return "", 204

    def delete(self, base_id, id):
        count = self.relation_model.delete().where(
            getattr(self.relation_model, self.relation_key_to_base) == base_id
            ,
            getattr(self.relation_model, self.relation_key_to_sub) == id
        ).execute()
        if count > 0:
            return "", 204
        else:
            return "Resource Does not exist", 404
