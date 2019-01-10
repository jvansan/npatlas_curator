import os
import logging
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from celery import Celery

# local imports
from config import app_config
app_config['CELERY_BROKER_URL'] = 'redis://127.0.0.1:6379/0'
app_config['CELERY_RESULT_BACKEND'] = 'redis://127.0.0.1:6379/0'

# initialze app variables
bootstrap = Bootstrap()
celery = Celery(__name__, broker=app_config['CELERY_BROKER_URL'], backend=app_config['CELERY_RESULT_BACKEND'])
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name):
    # Create app and set config
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')

    # initialze db, bootstrap, celery and login manager
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message = "You must login to access this page."
    login_manager.login_view = "auth.login"
    migrate = Migrate(app, db)
    celery.conf.update(app.config)

    from app import models

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, prefix='/admin')
    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)
    from .data import data as data_blueprint
    app.register_blueprint(data_blueprint, prefix='/data')
    from .checker import checker as checker_blueprint
    app.register_blueprint(checker_blueprint)

    @app.before_first_request
    def setup_logging():
        if not app.debug:
            # In production mode, add log handler to sys.stderr.
            app.logger.addHandler(logging.StreamHandler())
            app.logger.setLevel(logging.INFO)

    @app.errorhandler(403)
    def forbidden(error):
        return render_template('errors/403.html', title="Forbidden"), 403

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template('errors/404.html', title="Page Not Found"), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template('errors/500.html', title="Server Error"), 500

    return app
