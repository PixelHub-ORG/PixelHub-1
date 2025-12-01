import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from core.configuration.configuration import get_app_version
from core.managers.config_manager import ConfigManager
from core.managers.error_handler_manager import ErrorHandlerManager
from core.managers.logging_manager import LoggingManager
from core.managers.module_manager import ModuleManager

# Load environment variables
load_dotenv()

# Create the instances
db = SQLAlchemy()
migrate = Migrate()
oauth = OAuth()


def create_app(config_name="development"):
    app = Flask(__name__)

    # Load configuration according to environment
    config_manager = ConfigManager(app)
    config_manager.load_config(config_name=config_name)

    # Load ORCID config from .env
    app.config["ORCID_CLIENT_ID"] = os.environ.get("ORCID_CLIENT_ID")
    app.config["ORCID_CLIENT_SECRET"] = os.environ.get("ORCID_CLIENT_SECRET")
    app.config["FAKENODO_URL"] = os.environ.get("FAKENODO_URL", "https://zenodo.org")

    # Initialize SQLAlchemy and Migrate with the app
    db.init_app(app)
    migrate.init_app(app, db)
    oauth.init_app(app)

    # Register the ORCID client
    oauth.register(
        name="orcid",
        client_id=app.config["ORCID_CLIENT_ID"],
        client_secret=app.config["ORCID_CLIENT_SECRET"],
        authorize_url="https://orcid.org/oauth/authorize",
        access_token_url="https://orcid.org/oauth/token",
        client_kwargs={"scope": "/authenticate"},
        userinfo_compliance_fix=lambda token: {"sub": token.get("orcid")},
    )

    # Register modules
    module_manager = ModuleManager(app)
    module_manager.register_modules()

    # el medium WI
    from app.modules.badge.routes import badge_bp

    app.register_blueprint(badge_bp)

    # Register login manager
    from flask_login import LoginManager

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        from app.modules.auth.models import User

        return User.query.get(int(user_id))

    # Set up logging
    logging_manager = LoggingManager(app)
    logging_manager.setup_logging()

    # Initialize error handler manager
    error_handler_manager = ErrorHandlerManager(app)
    error_handler_manager.register_error_handlers()

    # Injecting environment variables into jinja context
    @app.context_processor
    def inject_vars_into_jinja():
        return {
            "FLASK_APP_NAME": os.getenv("FLASK_APP_NAME"),
            "FLASK_ENV": os.getenv("FLASK_ENV"),
            "DOMAIN": os.getenv("DOMAIN", "localhost"),
            "APP_VERSION": get_app_version(),
            "FAKENODO_URL": os.getenv("FAKENODO_URL", "https://zenodo.org"),
        }

    return app


app = create_app()
