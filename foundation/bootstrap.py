import os

from flask import Flask

from .db import db
from .routes import bp


P0_DEFAULT_DB = "sqlite:///partnershub_p0.db"


def register_foundation(app: Flask) -> Flask:
    """Attach the P0 persistence/auth foundation without changing legacy routes."""
    database_url = os.getenv("DATABASE_URL", P0_DEFAULT_DB)
    # Railway/Heroku-style DATABASE_URL values may use postgres://.
    if database_url.startswith("postgres://"):
        database_url = "postgresql+psycopg://" + database_url[len("postgres://"):]

    app.config.setdefault("SQLALCHEMY_DATABASE_URI", database_url)
    app.config.setdefault("SQLALCHEMY_TRACK_MODIFICATIONS", False)
    db.init_app(app)
    app.register_blueprint(bp)
    return app
