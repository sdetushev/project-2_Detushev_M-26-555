import ast


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
