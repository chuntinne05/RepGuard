"""Restricted Decimal interpreter and exact source-cell binding. Never eval/exec.

Passing this checker establishes source binding and arithmetic consistency only.
It does not establish that a program answers the natural-language question.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation, localcontext


def norm(value):
    return " ".join(unicodedata.normalize("NFKC", str(value)).split()).casefold()


def number(value):
    if isinstance(value, bool) or value is None:
        raise ValueError("Not a numeric value")
    text = str(value).strip().replace("−", "-").replace(",", "").replace("\u00a0", "")
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", text):
        raise ValueError("Noncanonical number")
    result = Decimal(text)
    if not result.is_finite() or abs(result) > Decimal("1e30"):
        raise ValueError("Number out of bounds")
    return result


def expanded_headers(headers):
    """Preserve raw headers and explicitly inherit metric for bare year columns.

    Example SALES REVENUE 2015 | 2014 becomes SALES REVENUE 2014.
    This deterministic interpretation is logged and is not semantic adjudication.
    """
    result, prefix = [], ""
    for raw in headers:
        text = " ".join(str(raw).split())
        if re.fullmatch(r"(?:19|20)\d{2}", text) and prefix:
            text = prefix + " " + text
        match = re.fullmatch(r"(.+?)\s+((?:19|20)\d{2})", text)
        if match:
            prefix = match[1]
        elif not re.fullmatch(r"(?:19|20)\d{2}", text):
            prefix = ""
        result.append(text)
    return result


def source_table(context):
    headers = context["merged_headers"]
    full = expanded_headers(headers)
    cells = []
    for ri, row in enumerate(context["rows"]):
        for ci, value in enumerate(row):
            if ci == 0:
                continue
            cells.append({"id": f"r{ri}c{ci}", "row_index": ri, "column_index": ci,
                          "row": str(row[0]), "column": full[ci] if ci < len(full) else "",
                          "raw_column": str(headers[ci]) if ci < len(headers) else "",
                          "value": str(value)})
    return {"table_id": context["table_id"], "doc_id": context["doc_id"],
            "year": context["year"], "page": context["page"], "title": context["title"],
            "headers": headers, "expanded_headers": full, "cells": cells}


def bind(cell, table):
    if cell.get("table_id") != table["table_id"]:
        raise ValueError("Wrong source table")
    rows = [c for c in table["cells"] if norm(c["row"]) == norm(cell.get("row", ""))]
    exact = [c for c in rows if norm(c["column"]) == norm(cell.get("col", ""))]
    if not exact:
        exact = [c for c in rows if norm(c["raw_column"]) == norm(cell.get("col", ""))]
    if len(exact) > 1 and any(k in cell for k in ("value", "cell_text")):
        # Public source contains repeated bare year headers. A published operand
        # may disambiguate only by an exact match to an actual source value.
        declared = cell.get("value", cell.get("cell_text"))
        exact = [c for c in exact if _same_numeric(c["value"], declared)]
    if len(exact) != 1:
        raise ValueError("Missing or ambiguous row/column")
    actual = exact[0]
    for key in ("value", "cell_text"):
        if key in cell and number(cell[key]) != number(actual["value"]):
            raise ValueError("Declared operand disagrees with source")
    number(actual["value"])
    return actual


def _same_numeric(a, b):
    try:
        return number(a) == number(b)
    except ValueError:
        return False


OPS = {"add", "sub", "mul", "div", "abs", "sum", "avg", "min", "max", "count"}


def execute(program, table, *, gold=False):
    """Source reads use IDs (prediction) or exact row/column refs (gold).

    Constants are restricted to 0,1,100,1000,1e6,1e9 for scale/percent only;
    source values cannot be smuggled as arbitrary literal operands.
    Registers must be unique and read before use. Max64 steps.
    """
    if not isinstance(program, list) or not 1 <= len(program) <= 64:
        raise ValueError("Invalid program size")
    regs, used = {}, []
    by_id = {c["id"]: c for c in table["cells"]}
    last = None
    with localcontext() as ctx:
        ctx.prec = 40
        for step in program:
            alias, op = step.get("as"), step.get("op")
            if not isinstance(alias, str) or not alias or alias in regs:
                raise ValueError("Register missing or reused")
            if op == "read":
                if gold:
                    cell = bind(step.get("cell", {}), table)
                else:
                    if step.get("cell_id") not in by_id:
                        raise ValueError("Unknown cell ID")
                    cell = by_id[step["cell_id"]]
                    if "value" in step and number(step["value"]) != number(cell["value"]):
                        raise ValueError("Forged source value")
                last = number(cell["value"])
                used.append(cell["id"])
            elif op in OPS:
                inputs = step.get("inputs", [])
                if not isinstance(inputs, list) or not inputs or len(inputs) > 32:
                    raise ValueError("Invalid operands")
                args = []
                for operand in inputs:
                    if isinstance(operand, str) and operand in regs:
                        args.append(regs[operand])
                    else:
                        literal = number(operand)
                        if literal not in {Decimal(x) for x in (0, 1, 100, 1000, 1000000, 1000000000)}:
                            raise ValueError("Non-scale literal")
                        args.append(literal)
                if op == "add":
                    last = sum(args)
                elif op in {"sub", "mul", "div"}:
                    if len(args) != 2:
                        raise ValueError("Binary arity")
                    a, b = args
                    if op == "sub": last = a - b
                    elif op == "mul": last = a * b
                    elif b == 0: raise ValueError("Division by zero")
                    else: last = a / b
                elif op == "abs":
                    if len(args) != 1: raise ValueError("Unary arity")
                    last = abs(args[0])
                elif op == "sum": last = sum(args)
                elif op == "avg": last = sum(args) / len(args)
                elif op == "min": last = min(args)
                elif op == "max": last = max(args)
                else: last = Decimal(len(args))
            else:
                raise ValueError("Unsupported operation")
            if not last.is_finite() or abs(last) > Decimal("1e30"):
                raise ValueError("Unbounded computation")
            regs[alias] = last
    if not used:
        raise ValueError("No source operands")
    return last, used


def close(a, b, tolerance=Decimal("0.005000001")):
    return abs(number(a) - number(b)) <= tolerance
