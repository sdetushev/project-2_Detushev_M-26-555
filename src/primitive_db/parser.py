import shlex


def parse_value(value: str) -> int | str | bool:
    """Convert a string representation into a Python value."""
    value = value.strip()

    if value.lower() == "true":
        return True

    if value.lower() == "false":
        return False

    if value.startswith(('"', "'")):
        quote = value[0]
        escaped = False
        for index, char in enumerate(value[1:], start=1):
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote and index != len(value) - 1:
                raise ValueError(f"Некорректное значение: {value}")
        if len(value) < 2 or value[-1] != value[0]:
            raise ValueError(f"Некорректное значение: {value}")

        try:
            lexer = shlex.shlex(value, posix=True)
            lexer.whitespace_split = True
            tokens = list(lexer)
        except ValueError:
            raise ValueError(f"Некорректное значение: {value}") from None

        if len(tokens) != 1:
            raise ValueError(f"Некорректное значение: {value}")

        return tokens[0]

    try:
        return int(value)
    except ValueError:
        raise ValueError(f"Некорректное значение: {value}") from None


def parse_condition(condition: str) -> dict:
    """Parse exactly one equality condition outside quoted strings."""
    quote = None
    escaped = False
    equal_index = None

    for index, char in enumerate(condition):
        if escaped:
            escaped = False
            continue
        if char == "\\" and quote is not None:
            escaped = True
            continue
        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None
            continue
        if char == "=" and quote is None:
            if equal_index is not None:
                raise ValueError(f"Некорректное условие: {condition}")
            equal_index = index

    if quote is not None or equal_index is None:
        raise ValueError(f"Некорректное условие: {condition}")

    column = condition[:equal_index].strip()
    value = condition[equal_index + 1 :].strip()

    if (
        not column
        or not value
        or not (
            column[0].isascii()
            and (column[0].isalpha() or column[0] == "_")
            and all(
                char.isascii() and (char.isalnum() or char == "_") for char in column
            )
        )
    ):
        raise ValueError(f"Некорректное условие: {condition}")

    return {column: parse_value(value)}


def split_command(user_input: str) -> list[str]:
    """Split a command while preserving quoted strings."""
    parts = []
    current = []
    quote = None
    escaped = False

    for char in user_input:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and quote is not None:
            current.append(char)
            escaped = True
            continue

        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None

            current.append(char)
            continue

        if char.isspace() and quote is None:
            if current:
                parts.append("".join(current))
                current = []
            continue

        current.append(char)

    if quote is not None or escaped:
        raise ValueError("Некорректный синтаксис команды.")

    if current:
        parts.append("".join(current))

    return parts


def parse_where(user_input: str, command: str) -> dict:
    """Extract and parse the WHERE condition from a command."""
    parts = split_command(user_input)

    if command not in ("select", "delete"):
        raise ValueError("Некорректное условие WHERE.")

    if (
        len(parts) < 5
        or parts[0] != command
        or parts[1] != "from"
        or parts[3] != "where"
    ):
        raise ValueError("Некорректное условие WHERE.")

    condition = " ".join(parts[4:])

    return parse_condition(condition)


def parse_update(user_input: str) -> tuple[dict, dict]:
    """Extract and parse SET and WHERE clauses from an UPDATE command."""
    parts = split_command(user_input)

    if len(parts) < 6 or parts[0] != "update" or parts[2] != "set":
        raise ValueError("Отсутствует или некорректно указано WHERE.")

    where_index = None

    for index in range(3, len(parts)):
        if parts[index] == "where":
            where_index = index
            break

    if where_index is None:
        raise ValueError("Отсутствует или некорректно указано WHERE.")

    set_text = " ".join(parts[3:where_index])
    where_text = " ".join(parts[where_index + 1 :])

    if not set_text or not where_text:
        raise ValueError("Отсутствует или некорректно указано WHERE.")

    set_clause = parse_condition(set_text)
    where_clause = parse_condition(where_text)

    return set_clause, where_clause


def parse_values(user_input: str) -> list:
    """Extract and parse values from an INSERT command."""
    parts = user_input.split(maxsplit=4)

    if (
        len(parts) != 5
        or parts[0] != "insert"
        or parts[1] != "into"
        or parts[3] != "values"
    ):
        raise ValueError("Некорректный синтаксис команды insert.")

    values_text = parts[4].strip()

    if not values_text.startswith("(") or not values_text.endswith(")"):
        raise ValueError("Значения должны находиться в скобках.")

    values_text = values_text[1:-1]

    values = []
    current = []
    quote = None
    escaped = False

    for char in values_text:
        if escaped:
            current.append(char)
            escaped = False
            continue

        if char == "\\" and quote is not None:
            current.append(char)
            escaped = True
            continue

        if char in ('"', "'"):
            if quote is None:
                quote = char
            elif quote == char:
                quote = None

            current.append(char)
            continue

        if quote is None and char in ("(", ")"):
            raise ValueError("Некорректный синтаксис значений.")

        if char == "," and quote is None:
            value = "".join(current).strip()

            if not value:
                raise ValueError("Некорректный синтаксис значений.")

            values.append(parse_value(value))
            current = []
            continue

        current.append(char)

    if quote is not None or escaped:
        raise ValueError("Некорректный синтаксис значений.")

    value = "".join(current).strip()

    if not value:
        raise ValueError("Некорректный синтаксис значений.")

    values.append(parse_value(value))

    return values
