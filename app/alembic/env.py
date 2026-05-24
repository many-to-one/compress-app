from logging.config import fileConfig
import os

from sqlalchemy import create_engine
from alembic import context

# Alembic Config
config = context.config

# Logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# =========================
# IMPORT MODELI (WAŻNE)
# =========================
from db.session import Base
from models.user import *  # <- dodaj wszystkie modele tutaj
# import db.models.other_model

target_metadata = Base.metadata


# =========================
# RUN MIGRATIONS OFFLINE
# =========================
def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# =========================
# RUN MIGRATIONS ONLINE
# =========================
def run_migrations_online():

    database_url = config.get_main_option("sqlalchemy.url")

    # 🔥 FIX: asyncpg -> psycopg2 (Alembic musi być sync)
    sync_url = database_url.replace("+asyncpg", "+psycopg2")

    connectable = create_engine(
        sync_url,
        pool_pre_ping=True,
    )

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# =========================
# ENTRYPOINT
# =========================
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()