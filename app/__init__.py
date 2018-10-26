import os
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# local imports
from config import app_config

# initialze app variables
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name):
    # Create app and set config
    # TODO: Production environment
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(app_config[config_name])
    app.config.from_pyfile('config.py')


    # initialze db, bootstrap, and login manager
    Bootstrap(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_message = "You must login to access this page."
    login_manager.login_view = "auth.login"
    migrate = Migrate(app, db)

    from app import models

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, prefix='/admin')
    from .home import home as home_blueprint
    app.register_blueprint(home_blueprint)
    from .data import data as data_blueprint
    app.register_blueprint(data_blueprint, prefix='/data')

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
