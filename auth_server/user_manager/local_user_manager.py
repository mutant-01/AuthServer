from auth_server.models import auth_model
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
