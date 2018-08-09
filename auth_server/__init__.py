import os
from datetime import timedelta
from flask import Flask
from logging.config import dictConfig
import sys
from flask_jwt_extended import JWTManager
from playhouse.flask_utils import FlaskDB
from playhouse.db_url import connect


# lazy extensions
db = connect(
    os.environ.get(
        "DATABASE_URI", "postgres://postgres@postgres:5432/auth"
    ),
)
db_wrapper = FlaskDB(database=db)
jwt = JWTManager()


def create_app(extra_configs: dict=None) -> Flask:
    """Creates the application object

    :param extra_configs: the dictionary from which the flask app.config updates from. it overrides the default configs.
    """
    app = Flask(__name__)

    # set logging
    level = os.environ.get("LOG_LEVEL", default='INFO').upper()
    prefix = os.environ.get("LOG_PREFIX", default="AuthServer")
    set_logging(level=level, prefix=prefix)

    # jwt flask extended
    jwt.init_app(app)
    jwt_secret = os.environ.get("JWT_SECRET_KEY", None)
    if jwt_secret is None:
        raise TypeError("no JWT_SECRET_KEY env variable")
    app.config["JWT_SECRET_KEY"] = jwt_secret
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        minutes=int(os.environ.get("JWT_ACCESS_TOKEN_EXPIRES", 10803))
    )
    app.config["JWT_HEADER_NAME"] = os.environ.get("JWT_HEADER_NAME", "Authorization")
    app.config["JWT_HEADER_TYPE"] = os.environ.get("JWT_HEADER_TYPE", "Bearer")
    app.config['JWT_BLACKLIST_ENABLED'] = True
    app.config['JWT_BLACKLIST_TOKEN_CHECKS'] = ['access']
    import auth_server.utils.jwt

    # peewee
    db_wrapper.init_app(app)

    if extra_configs is not None:
        app.config.update(extra_configs)

    # blueprints
    from auth_server.views.auth_views import auth_bp
    app.register_blueprint(auth_bp)

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

