from flask import Flask

from app.routes import api_bp


def create_app() -> Flask:
    """Application factory for the fakenodo service."""
    app = Flask(__name__)

    # Register API blueprint under /api
    app.register_blueprint(api_bp, url_prefix="/api")

    # Health check
    @app.get("/health")
    def health():  # pragma: no cover
        return {"status": "ok"}, 200

    return app
