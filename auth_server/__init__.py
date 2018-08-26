import os
from datetime import timedelta
from flask import Flask, send_from_directory
from logging.config import dictConfig
import sys
from flask.views import MethodView
from flask_jwt_extended import JWTManager
from flask_swagger_ui import get_swaggerui_blueprint
from playhouse.flask_utils import FlaskDB
from playhouse.db_url import connect
from auth_server import config


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

    # redis config
    app.config["REDIS_HOST"] = os.environ.get("REDIS_HOST", "redis")
    app.config["REDIS_PORT"] = int(os.environ.get("REDIS_PORT", 6379))
    app.config["REDIS_BLACKLIST"] = os.environ.get("REDIS.GENERAL", "blacklist")

    if extra_configs is not None:
        app.config.update(extra_configs)

    # add swagger ui
    set_api_doc(app)

    # blueprints
    from auth_server.views.auth_views import auth_bp
    app.register_blueprint(auth_bp)
    from auth_server.views.identity_views import identity_bp
    app.register_blueprint(identity_bp)

    # methodViews
    from auth_server.views.identity_views import UsersView
    register_methodview(app, UsersView, "users")
    from auth_server.views.identity_views import RolesView
    register_methodview(app, RolesView, "roles")
    from auth_server.views.identity_views import ResourcesView
    register_methodview(app, ResourcesView, "resources")
    from auth_server.views.identity_views import UserRolesView
    register_methodview(app, UserRolesView, "roles", url_prefix='/users/<string:base_id>')
    from auth_server.views.identity_views import RoleUsersView
    register_methodview(app, RoleUsersView, "users", url_prefix='/roles/<string:base_id>')
    from auth_server.views.identity_views import RoleResourcesView
    register_methodview(app, RoleResourcesView, "resources", url_prefix='/roles/<string:base_id>')
    from auth_server.views.identity_views import ResourceRolesView
    register_methodview(app, ResourceRolesView, "roles", url_prefix='/resources/<string:base_id>')

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


def register_methodview(app: Flask, m_view: MethodView, path: str, url_prefix=''):
    """Registers new MethodView to flask app

    All HTTP verbs are registered by default one should implement all of them(GET, POST, PUT, DELETE) and return 405
    if there is no need for the specific verb.
    :param app: the flask application instance in which the method view should be registered in.
    :param m_view: the MethodView class that should be registered.
    :param path: the relative path to the endpoint(relative to url_prefix arg)
    :param url_prefix: prefix to be prepended to the path arg
    """
    view_func = m_view.as_view(url_prefix.replace('/', '') + path.replace('/', ''))
    if url_prefix and not url_prefix.startswith('/'):
        url_prefix = '/' + url_prefix
    if not path.startswith('/'):
        path = '/' + path
    app.add_url_rule(
        '{}{}'.format(url_prefix, path),
        defaults={'id': None},
        view_func=view_func,
        methods=['GET', ]
    )
    app.add_url_rule(
        '{}{}'.format(url_prefix, path),
        view_func=view_func,
        methods=['POST', ]
    )
    app.add_url_rule(
        '{}{}/<string:id>'.format(url_prefix, path),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE', 'PATCH']
    )


def set_api_doc(app: Flask):
    api_yaml_url = config.url_prefix + '/api_doc_file'
    api_doc = config.url_prefix + "/api_docs"
    swaggerui_blueprint = get_swaggerui_blueprint(
        api_doc,
        api_yaml_url
    )
    app.register_blueprint(swaggerui_blueprint, url_prefix=api_doc)

    @app.route(api_yaml_url)
    def api_doc():
        return send_from_directory('static', 'OAS.yaml')
