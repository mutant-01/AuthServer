from logging import getLogger
from flask import request
from flask.views import MethodView
from marshmallow import Schema, ValidationError
from peewee import DoesNotExist, IntegrityError
from auth_server import db_wrapper


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
