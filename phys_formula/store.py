"""SQLite persistence for the single shared chat thread (SQLModel, bundled with reflex[db])."""

from __future__ import annotations

from datetime import datetime, timezone

import reflex as rx
import sqlalchemy
from sqlmodel import Field, Session, SQLModel, select

_engines: dict[str, sqlalchemy.engine.Engine] = {}
_url_override: str | None = None


class Message(SQLModel, table=True):
    """One chat turn. Role is ``user`` or ``assistant``."""

    id: int | None = Field(default=None, primary_key=True)
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def configure(url: str | None) -> None:
    """Override the DB URL (tests point this at a temp file). ``None`` restores rxconfig's."""
    global _url_override
    _url_override = url


def _engine() -> sqlalchemy.engine.Engine:
    url = _url_override or rx.config.get_config().db_url
    if url is None:
        raise ValueError("No db_url configured in rxconfig.py")
    if url not in _engines:
        _engines[url] = sqlalchemy.create_engine(url)
        SQLModel.metadata.create_all(_engines[url])
    return _engines[url]


def save_message(role: str, content: str) -> None:
    with Session(_engine()) as s:
        s.add(Message(role=role, content=content))
        s.commit()


def load_messages() -> list[dict[str, str]]:
    with Session(_engine()) as s:
        rows = s.exec(select(Message).order_by(Message.id)).all()
    return [{"role": r.role, "content": r.content} for r in rows]
