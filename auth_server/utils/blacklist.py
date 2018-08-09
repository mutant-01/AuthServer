import datetime
import redis
from flask import current_app
import time


class UserBlackList:
    __epoch = datetime.datetime(1970, 1, 1)

    def __init__(self):
        self.__login_exp = current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
        self.__redis_blacklist = current_app.config["REDIS_BLACKLIST"]
        self.__redis = redis.StrictRedis(
            host=current_app.config['REDIS_HOST'],
            port=current_app.config['REDIS_PORT']
        )

    @classmethod
    def __sec_from_epoch(cls, dt: datetime.datetime) -> float:
        return (dt - cls.__epoch).total_seconds()

    def persist_token_in_blacklist(self, token):
        pipeline = self.__redis.pipeline()
        pipeline.zremrangebyscore(
            self.__redis_blacklist, '-inf',
            self.__sec_from_epoch(datetime.datetime.utcnow() - self.__login_exp)
        )
        pipeline.zadd(self.__redis_blacklist, time.time(), token)
        pipeline.execute()

    def token_in_blacklist(self, token) -> bool:
        """Checks if token in blacklist

        :returns bool: True if token in blacklist and False otherwise
        """
        pipeline = self.__redis.pipeline()
        pipeline.zremrangebyscore(
            self.__redis_blacklist, '-inf',
            self.__sec_from_epoch(datetime.datetime.utcnow() - self.__login_exp)
        )
        pipeline.zscore(self.__redis_blacklist, token)
        result = pipeline.execute()
        if result[1] is None:
            return False
        else:
            return True
