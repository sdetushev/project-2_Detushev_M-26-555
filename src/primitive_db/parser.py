import ast
import re


def parse_value(value: str) -> int | str | bool:
    """Convert a string representation into a Python value."""
    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    try:
        parsed = ast.literal_eval(value)
    except (ValueError, SyntaxError):
        raise ValueError(f"Некорректное значение: {value}") from None

    if type(parsed) not in (int, str, bool):
        raise ValueError(f"Некорректное значение: {value}")

    return parsed


def parse_condition(condition: str) -> dict:
    """Parse a column equality condition into a dictionary."""
    parts = condition.split("=", maxsplit=1)

    if len(parts) != 2:
        raise ValueError(f"Некорректное условие: {condition}")

    column = parts[0].strip()
    value = parts[1].strip()

    if not column or not value:
        raise ValueError(f"Некорректное условие: {condition}")

    return {column: parse_value(value)}


def parse_where(user_input: str, command: str) -> dict:
    """Extract and parse the WHERE condition from a command."""
    pattern = rf"^\s*{command}\s+(?:from\s+)?\S+\s+where\s+(.+)$"
    match = re.match(pattern, user_input)

    if match is None:
        raise ValueError("Некорректное условие WHERE.")

    return parse_condition(match.group(1).strip())


def parse_update(user_input: str) -> tuple[dict, dict]:
    """Extract and parse SET and WHERE clauses from an UPDATE command."""
    pattern = (
        r"^\s*update\s+\S+\s+set\s+"
        r"""((?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^"'])*?)"""
        r"\s+where\s+(.+)$"
    )

    match = re.match(pattern, user_input)

    if match is None:
        raise ValueError("Отсутствует или некорректно указано WHERE.")

    set_clause = parse_condition(match.group(1).strip())
    where_clause = parse_condition(match.group(2).strip())

    return set_clause, where_clause


def parse_values(user_input: str) -> list:
    """Extract and parse values from an INSERT command."""
    match = re.match(
        r"^\s*insert\s+into\s+\S+\s+values\s+(.+)$",
        user_input,
    )

    if match is None:
        raise ValueError("Некорректный синтаксис команды insert.")

    values_text = match.group(1).strip()

    if not values_text.startswith("(") or not values_text.endswith(")"):
        raise ValueError("Значения должны находиться в скобках.")

    values_text = values_text[1:-1]

    values_text = re.sub(
        r'("(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|\btrue\b|\bfalse\b)',
        lambda match: (
            match.group(0)
            if match.group(0).startswith(('"', "'"))
            else match.group(0).capitalize()
        ),
        values_text,
        flags=re.IGNORECASE,
    )

    return list(ast.literal_eval(f"[{values_text}]"))
