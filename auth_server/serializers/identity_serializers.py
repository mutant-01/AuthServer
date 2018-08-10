from marshmallow import Schema, fields, validate, post_load
from auth_server.utils.password import hash_password


class UserSerializer(Schema):
    id = fields.Int(dump_only=True)
    username = fields.Str(validate=validate.Length(max=128, min=1), required=True)
    password = fields.Str(validate=validate.Length(max=256, min=8), load_only=True, required=True)

    @post_load
    def hash_password(self, data):
        data["password"] = hash_password(data["password"])
        return data


class RoleSerializer(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(validate=validate.Length(max=256), required=True)
    description = fields.Str()


class ResourceSerializer(Schema):
    id = fields.Int(dump_only=True)
    path = fields.Str(validate=validate.Length(max=1024, min=1), required=True)