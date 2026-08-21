import json
import re
from collections.abc import Iterator
from typing import Any


def extract_assignment_json(html: str, marker: str) -> dict[str, Any] | None:
    marker_index = html.find(marker)
    if marker_index < 0:
        return None
    start = html.find("{", marker_index + len(marker))
    if start < 0:
        return None

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(html)):
        char = html[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                raw = html[start : index + 1]
                raw = re.sub(r"(:|,)\s*undefined(?=\s*[,}\]])", r"\1null", raw)
                try:
                    value = json.loads(raw)
                except json.JSONDecodeError:
                    return None
                return value if isinstance(value, dict) else None
    return None


def walk_dicts(value: object, *, max_depth: int = 8) -> Iterator[dict[str, Any]]:
    stack: list[tuple[object, int]] = [(value, 0)]
    while stack:
        current, depth = stack.pop()
        if depth > max_depth:
            continue
        if isinstance(current, dict):
            yield current
            stack.extend((child, depth + 1) for child in current.values())
        elif isinstance(current, list):
            stack.extend((child, depth + 1) for child in current)


def first_url(value: object) -> str | None:
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value.replace("\\u002F", "/").replace("\\/", "/")
    if isinstance(value, list):
        for item in value:
            result = first_url(item)
            if result:
                return result
    if isinstance(value, dict):
        for key in ("url", "masterUrl", "urlDefault", "url_list", "urlList"):
            result = first_url(value.get(key))
            if result:
                return result
    return None
