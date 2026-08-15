from logging.config import fileConfig
import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from foundation.db import db
from foundation import models  # noqa: F401 - registers base metadata models
from foundation import models_p4, models_p5, models_p6, models_p7, models_p8, models_p9, models_p10, models_p11, models_p12, models_p13, models_p14, models_p15, models_p16, models_p18  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = db.metadata


def database_url() -> str:
    url = os.getenv("DATABASE_URL", "sqlite:///partnershub_p0.db")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    return url


def run_migrations_offline() -> None:
    context.configure(url=database_url(), target_metadata=target_metadata, literal_binds=True, compare_type=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = database_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata, compare_type=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
