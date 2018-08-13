from auth_server.serializers import auth_serializers, identity_serializers
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin

spec = APISpec(
    title='auth-server',
    version='1.0.0',
    openapi_version='3.0',
    plugins=(MarshmallowPlugin(), )
)

# auth serializers
spec.definition("token-input", schema=auth_serializers.TokenInput)
spec.definition("token-output", schema=auth_serializers.TokenOutput)
spec.definition("authorize-input", schema=auth_serializers.AuthorizeInput)
spec.definition("token-output", schema=auth_serializers.AuthorizeOutput)

# identity serializers
spec.definition("id-schema", schema=identity_serializers.IdSerializer)
spec.definition("user-schema", schema=identity_serializers.UserSerializer)
spec.definition("role-schema", schema=identity_serializers.RoleSerializer)
spec.definition("resource-schema", schema=identity_serializers.ResourceSerializer)

print(spec.to_yaml())
