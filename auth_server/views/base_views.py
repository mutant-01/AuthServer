from logging import getLogger
from flask import request
from flask.views import MethodView
from marshmallow import Schema, ValidationError
from auth_server.models.auth_model import get_all_many_many_as_sub, get_one_many_many_as_sub, insert_to_table, \
    delete_from_relation_table
from auth_server.models.errors import DoesNotExist, DuplicateConstraint, ConstraintViolation
from auth_server.models.utils import CrudModel
from auth_server.serializers.identity_serializers import IdSerializer


class BasicCrudView(MethodView):
    """The class is meant to be inherited"""

    # should be a CrudModel mixedIn
    model = CrudModel

    # should be a Marshmallow schema
    serializer = Schema

    def get(self, id):
        """Returns all resources or one by id"""
        # returns all records of the model
        if id is None:
            return self.serializer().dumps(self.model.get_all(), many=True), 200
        # returns a record by id
        else:
            try:
                record = self.model.get_by_id(id=id)
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
                id = self.model.create(data)
            except DuplicateConstraint:
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
                self.model.update(id=id, data=data)
            except DoesNotExist:
                return "Resource Does not exist", 404
            except DuplicateConstraint:
                return "Resource with same constrained values already exists", 409
            return "", 204

    def delete(self, id):
        try:
            self.model.delete(id)
        except DoesNotExist:
            return "Resource Does not exist", 404
        return "", 204


class ManyManySubResource(MethodView):
    """represent a many to many relation as sub resource.

    the relation must be assumed to have a direction from one of source tables,
     in which source table is the base model and the target table is sub model"""
    base_model = None
    # relation table as type sqlAlchemy Table
    relation_table = None
    # the foreign key from relation table to base model
    relation_field_to_base = ''
    # the foreign key from relation table to sub model
    relation_field_to_sub = ''
    sub_model = None
    # fields to fetch from sub model
    fields = []

    # sub resource serializer
    serializer = Schema

    def get(self, base_id, id):
        """Returns all resources or one by id"""
        serializer_obj = self.serializer()
        # returns all records of the model
        if id is None:
            db_data = get_all_many_many_as_sub(
                self.base_model, self.sub_model, self.relation_table,
                self.relation_field_to_base, self.relation_field_to_sub, base_id, self.fields
            )
            return serializer_obj.dumps(db_data, many=True), 200
        # returns a record by id
        else:
            db_data = get_one_many_many_as_sub(
                self.base_model, self.sub_model, self.relation_table,
                self.relation_field_to_base, self.relation_field_to_sub, base_id, id, self.fields
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
            data[self.relation_field_to_base] = base_id
            data[self.relation_field_to_sub] = data.pop("id")
            try:
                insert_to_table(self.relation_table, data)
            except ConstraintViolation:
                return "Resource already exists or system constraint", 409
            return "", 204

    def delete(self, base_id, id):
        r = delete_from_relation_table(
            self.relation_table,
            self.relation_field_to_base,
            self.relation_field_to_sub,
            base_id,
            id
        )
        if r:
            return "", 204
        else:
            return "Resource Does not exist", 404
