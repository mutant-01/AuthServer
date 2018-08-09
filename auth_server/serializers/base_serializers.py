from marshmallow import Schema, validates_schema, ValidationError


class StrictSchema(Schema):
    @validates_schema(pass_original=True)
    def check_unknown_fields(self, _, original_data):
        unknown = set(original_data) - set(self.fields)
        if unknown:
            raise ValidationError('Unknown field', list(unknown))