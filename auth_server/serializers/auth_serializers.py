from marshmallow import validate, fields, Schema

from auth_server.serializers.base_serializers import StrictSchema


class TokenInput(StrictSchema):
    username = fields.Str(validate=validate.Length(max=128), required=True)
    password = fields.Str(validate=validate.Length(max=128, min=8), required=True, load_only=True)


class TokenOutput(Schema):
    token = fields.Str(dump_only=True)


class Claims(Schema):
    class Meta:
        dateformat = "%Y-%m-%dT%H:%M:%S.%fZ"

    roles = fields.List(fields.Int())
    iss_dt = fields.DateTime()


class AuthorizeInput(StrictSchema):
    token = fields.Str(required=True, load_only=True)
    resources = fields.List(fields.Str(), required=True, load_only=True)


class AuthorizeOutput(Schema):
    token = fields.Str(required=True)
    resources = fields.Dict(values=fields.Bool(), keys=fields.Str())
