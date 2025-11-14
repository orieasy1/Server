import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

# ---------------------------------------------------------
# ★ FastAPI app path 추가 (상위 디렉토리 포함시키기)
# ---------------------------------------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ---------------------------------------------------------
# ★ FastAPI 설정 파일(settings) 및 Base import
# ---------------------------------------------------------
from app.core.config import settings
from app.models import Base

# ---------------------------------------------------------
# Alembic 설정 객체
# ---------------------------------------------------------
config = context.config

# Logging 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ---------------------------------------------------------
# Alembic이 추적할 metadata 설정
# ---------------------------------------------------------
target_metadata = Base.metadata


# ---------------------------------------------------------
# ★ DB URL을 FastAPI settings에서 가져온 것으로 override
# ---------------------------------------------------------
def get_url():
    return settings.DATABASE_URL


# ---------------------------------------------------------
# offline 모드 (SQL 출력만)
# ---------------------------------------------------------
def run_migrations_offline():
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------
# online 모드 (DB 연결 후 migration 실행)
# ---------------------------------------------------------
def run_migrations_online():
    # alembic.ini의 sqlalchemy.url을 FastAPI DB URL로 설정
    config.set_main_option("sqlalchemy.url", get_url())

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ---------------------------------------------------------
# 실행
# ---------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
