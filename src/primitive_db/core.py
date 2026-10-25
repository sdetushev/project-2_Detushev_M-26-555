from pathlib import Path

from primitive_db.utils import load_table_data


def create_table(
    metadata: dict,
    table_name: str,
    columns: list[str],
) -> dict:
    """Create a table with validated columns and an automatic ID field."""
    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    valid_types = {"int", "str", "bool"}
    parsed_columns = []

    for column in columns:
        parts = column.split(":")

        if len(parts) != 2 or not parts[0] or parts[1] not in valid_types:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        parsed_columns.append(column)

    if not any(column.split(":")[0] == "ID" for column in parsed_columns):
        parsed_columns.insert(0, "ID:int")

    metadata[table_name] = parsed_columns

    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{', '.join(parsed_columns)}"
    )

    return metadata


def drop_table(metadata: dict, table_name: str) -> dict:
    """Delete a table and its data file if it exists."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]

    filepath = Path("data") / f"{table_name}.json"
    filepath.unlink(missing_ok=True)

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata


def insert(
    metadata: dict,
    table_name: str,
    values: list,
) -> list[dict] | None:
    """Validate values and insert a new record into a table."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    columns = metadata[table_name]
    data = load_table_data(table_name)

    user_columns = [column for column in columns if column.split(":")[0] != "ID"]

    if len(values) != len(user_columns):
        print("Некорректное количество значений. Попробуйте снова.")
        return None

    record = {}

    for column, value in zip(user_columns, values, strict=True):
        column_name, column_type = column.split(":")

        if column_type == "int":
            valid = type(value) is int
        elif column_type == "str":
            valid = type(value) is str
        else:
            valid = type(value) is bool

        if not valid:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return None

        record[column_name] = value

    record_id = max((row["ID"] for row in data), default=0) + 1
    record = {"ID": record_id, **record}

    data.append(record)

    print(f'Запись с ID={record_id} успешно добавлена в таблицу "{table_name}".')

    return data


def select(
    table_data: list[dict],
    where_clause: dict | None = None,
) -> list[dict]:
    """Return all records or filter them by the given conditions."""
    if where_clause is None:
        return table_data

    return [
        record
        for record in table_data
        if all(record.get(column) == value for column, value in where_clause.items())
    ]


def update(
    table_data: list[dict],
    set_clause: dict,
    where_clause: dict,
) -> list[dict]:
    """Update records that match the given conditions."""
    for record in table_data:
        if all(record.get(column) == value for column, value in where_clause.items()):
            record.update(set_clause)
            print(f"Запись с ID={record['ID']} успешно обновлена.")

    return table_data


def delete(
    table_data: list[dict],
    where_clause: dict,
) -> list[dict]:
    """Delete records that match the given conditions."""
    remaining_data = []

    for record in table_data:
        if all(record.get(column) == value for column, value in where_clause.items()):
            print(f"Запись с ID={record['ID']} успешно удалена.")
        else:
            remaining_data.append(record)

    return remaining_data
