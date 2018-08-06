import os
from flask import Flask
from logging.config import dictConfig
import sys


def create_app(extra_configs: dict=None) -> Flask:
    """Creates the application object

    :param extra_configs: the dictionary from which the flask app.config updates from. it overrides the default configs.
    """
    app = Flask(__name__)

    # set logging
    level = os.environ.get("LOG_LEVEL", default='INFO').upper()
    prefix = os.environ.get("LOG_PREFIX", default="AuthServer")
    set_logging(level=level, prefix=prefix)

    if extra_configs is not None:
        app.config.update(extra_configs)

    return app


def set_logging(level='INFO', prefix=''):
    if level not in ("INFO", "DEBUG", "WARNING"):
        raise ValueError("LOG_LEVEL should be one of INFO, DEBUG or WARNING")
    dictConfig({
        'version': 1,
        'formatters': {'default': {
            'format': '{} [%(asctime)s] %(levelname)s in %(module)s: %(message)s'.format(prefix)
        }},
        'handlers': {'stream': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'default',
        }},
        'root': {
            'level': level,
            'handlers': ['stream']
        }
    })

