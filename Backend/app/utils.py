import json
from datetime import datetime
from typing import Any


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False)


def loads(value: str | None, default: Any) -> Any:
    if not value:
        return default
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return default


def iso(dt: datetime | None) -> str | None:
    return dt.isoformat() + "Z" if dt else None

