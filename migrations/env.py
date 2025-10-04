import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.db.database import Base
from app.db import models  # ให้ Alembic เห็นตารางทั้งหมด

# --- ใช้ชื่อ alembic_config แทน config เพื่อไม่ให้ชนกับ logging.config ---
alembic_config = context.config

# อ่าน DATABASE_URL จาก ENV (Render ตั้งไว้ใน Dashboard)
alembic_config.set_main_option("sqlalchemy.url", os.getenv("DATABASE_URL", ""))

# โหลด logging จาก alembic.ini ถ้ามี (ถ้าไม่มีก็ข้ามได้)
cfg_file = alembic_config.config_file_name
if cfg_file:
    try:
        fileConfig(cfg_file)
    except Exception:
        pass

target_metadata = Base.metadata


def run_migrations_offline():
    url = alembic_config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        alembic_config.get_section(alembic_config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
