# -*- coding:utf-8 -*-
'''
Basic root blueprint entry point.
'''
import flask
from .common import conf, pb_root
from .backend import init_db
from . import default


def setup_flask_session(flask_app):
    session_db = mongoengine.connection.get_db(alias=default.MONGOENGINE_ALIAS)
    config_dict = {
        "SESSION_COOKIE_NAME": conf.SESSION_COOKIE_NAME,
        "SESSION_TYPE": "mongodb",
        "SESSION_MONGODB": session_db.client,
        "SESSION_MONGODB_DB": session_db.name,
        "SESSION_MONGODB_COLLECT": "sessions",
        "PERMANENT_SESSION_LIFETIME": conf.PAULI_SESSION_LIFETIME
    }
    flask_app.config.update(config_dict)
    flask_session.Session(flask_app)


def setup_perm_broker(flask_app, url_prefix="/pb", **config):
    # write config to conf
    for k, v in config.items():
        setattr(conf, k, v)

    # setup database
    init_db(**config)

    # import sub level path routings
    from .user.views import api
    from .auth.views import api
    from .auth.views import web
    from .perm.views import api

    if conf.DEBUG and getattr(conf, 'ENABLE_DEBUG_LOGIN', False):
        from .auth.views import debug_api

    # bind pauli blueprint
    flask_app.register_blueprint(pb_root, url_prefix=url_prefix)


__ALL__ = ['pb_root', 'conf', 'setup_perm_broker']
