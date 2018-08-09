from abc import ABC, abstractmethod


class BaseUserManager(ABC):

    def __init__(self, username: str, **kwargs):
        self.username = username

    @abstractmethod
    def authenticate(self) -> dict:
        """

        :return: user from database or None if authentication fails
        """
        raise NotImplemented

    @abstractmethod
    def register(self):
        raise NotImplemented
