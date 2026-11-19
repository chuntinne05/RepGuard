"""Caller-owned adapters; never run arbitrary extraction code from an agent."""
from __future__ import annotations

import hashlib
import csv
import io
import json
from pathlib import Path

from .models import Fact, Scope


def json_pointer_fact(path: Path, pointer: str, *, fact_id: str, scope: Scope,
                      unit: str, source_id: str, root_ids: tuple[str, ...]) -> Fact:
    """Read a scalar from an immutable snapshot; semantic mapping remains external.

    Caller must approve scope/unit separately. A hash binds bytes, not meaning.
    """
    data = Path(path).read_bytes()
    obj = json.loads(data)
    if not pointer.startswith("/"):
        raise ValueError("Pointer must be absolute and nonempty")
    for token in pointer[1:].split("/"):
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(obj, list):
            if not token.isdigit(): raise ValueError("Invalid array index")
            obj = obj[int(token)]
        elif isinstance(obj, dict):
            obj = obj[token]
        else:
            raise ValueError("Pointer traverses scalar")
    if isinstance(obj, bool) or obj is None or isinstance(obj, (list, dict)):
        raise ValueError("Expected scalar fact")
    return Fact(id=fact_id, value=str(obj), unit=unit, scope=scope, source_id=source_id,
                snapshot_sha256=hashlib.sha256(data).hexdigest(), locator=pointer, root_ids=root_ids)


def csv_row_fact(path: Path, *, match: dict[str, str], value_column: str,
                 fact_id: str, scope: Scope, unit: str, source_id: str,
                 root_ids: tuple[str, ...]) -> Fact:
    """Exact unique-row extraction; ambiguity is never resolved by first match.

    UTF-8 CSV only. No locale guessing or silent unit/number normalization.
    """
    if not match:
        raise ValueError("Explicit row key required")
    data = Path(path).read_bytes()
    reader = csv.reader(io.StringIO(data.decode("utf-8-sig"), newline=""))
    headers = next(reader, [])
    if not headers or len(set(headers)) != len(headers) or any(not h for h in headers):
        raise ValueError("Ambiguous or missing CSV header")
    if value_column not in headers or not set(match) <= set(headers):
        raise ValueError("Unknown CSV column")
    selected = []
    for row_index, row in enumerate(reader, 1):
        if len(row) != len(headers):
            raise ValueError("Ragged CSV row")
        record = dict(zip(headers, row))
        if all(record[k] == v for k, v in match.items()):
            selected.append((row_index, record[value_column]))
    if len(selected) != 1:
        raise ValueError("Missing or ambiguous CSV row")
    index, value = selected[0]
    return Fact(id=fact_id, value=value, unit=unit, scope=scope, source_id=source_id,
                snapshot_sha256=hashlib.sha256(data).hexdigest(),
                locator=f"csv:row={index};column={value_column}", root_ids=root_ids)
