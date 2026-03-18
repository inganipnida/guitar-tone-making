from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import inspect, text
from sqlmodel import Session, SQLModel, create_engine

from app.config import settings


engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    _apply_sqlite_migrations()



def _apply_sqlite_migrations() -> None:
    with engine.begin() as connection:
        inspector = inspect(connection)
        if "analysisrecord" not in inspector.get_table_names():
            return
        columns = {column["name"] for column in inspector.get_columns("analysisrecord")}
        if "processed_filename" not in columns:
            connection.execute(
                text("ALTER TABLE analysisrecord ADD COLUMN processed_filename VARCHAR NOT NULL DEFAULT ''")
            )



def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
