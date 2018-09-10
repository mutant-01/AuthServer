from logging import getLogger
from auth_server.models import auth_model
from auth_server.models.auth_model import get_resources_by_roles
from auth_server.user_manager.abc_user_manager import BaseUserManager
from auth_server.utils.password import hash_password


class LocalUserManager(BaseUserManager):

    def __init__(self, username: str, **kwargs):
        super().__init__(username, **kwargs)
        try:
            self.password = kwargs["password"]
        except KeyError:
            raise TypeError("missing argument 'password'")
        else:
            self.password = hash_password(self.password)  # todo rainbow attack

    def register(self):
        raise NotImplementedError

    def authenticate(self) -> dict:
        """

        :return: user from database or None if authentication fails
        """
        return auth_model.get_user_by_user_pass(self.username, self.password)

    @staticmethod
    def authorize(roles: list, resources: list) -> dict:
        """Gets resources and role identifiers and returns a dict of resources/allow(bool) pair"""
        all_resources = set(resources)
        try:
            resource_value_list = get_resources_by_roles(roles=set(roles), resources=all_resources)
        except TypeError as e:
            getLogger().exception(e)
            getLogger().info("roles or resources empty, no resource allowed")
            resource_value_list = []
        # iterate over allowed resources which is a list of tuples(resource, value)
        result = {}
        for r, v in resource_value_list:
            result[r] = True if v is None else v
            all_resources.remove(r)
        result.update({r: False for r in all_resources})
        return result
