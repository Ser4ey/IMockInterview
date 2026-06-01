import json
from typing import Any


def dumps_list(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def loads_list(value: str | None) -> list[str]:
    if not value:
        return []
    try:
        payload: Any = json.loads(value)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [str(item) for item in payload]


def dumps_dict(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False)
