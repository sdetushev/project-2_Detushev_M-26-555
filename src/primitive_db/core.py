from primitive_db.constants import (
    ID_COLUMN,
    ID_COLUMN_DEFINITION,
    TYPE_MAPPING,
    VALID_TYPES,
)
from primitive_db.decorators import (
    confirm_action,
    handle_db_errors,
    log_time,
)


def is_valid_table_name(table_name: str) -> bool:
    """Check whether a table name contains only allowed ASCII characters."""
    if not table_name:
        return False

    first_char = table_name[0]

    if not ("A" <= first_char <= "Z" or "a" <= first_char <= "z" or first_char == "_"):
        return False

    for char in table_name[1:]:
        if not (
            "A" <= char <= "Z"
            or "a" <= char <= "z"
            or "0" <= char <= "9"
            or char == "_"
        ):
            return False

    return True


def matches_condition(record: dict, where_clause: dict) -> bool:
    """Check whether a record matches all conditions with strict types."""
    for column, value in where_clause.items():
        if column not in record:
            return False

        record_value = record[column]

        if type(record_value) is not type(value):
            return False

        if record_value != value:
            return False

    return True


@handle_db_errors
def create_table(
    metadata: dict,
    table_name: str,
    columns: list[str],
) -> dict:
    """Create a table with validated columns and an automatic ID field."""
    if not is_valid_table_name(table_name):
        print(
            "Ошибка: Имя таблицы должно содержать только латинские буквы, "
            "цифры и подчёркивания и не может начинаться с цифры."
        )
        return metadata

    if table_name in metadata:
        print(f'Ошибка: Таблица "{table_name}" уже существует.')
        return metadata

    parsed_columns = []
    column_names = {ID_COLUMN}

    for column in columns:
        parts = column.split(":")

        if len(parts) != 2 or not parts[0] or parts[1] not in VALID_TYPES:
            print(f"Некорректное значение: {column}. Попробуйте снова.")
            return metadata

        column_name = parts[0]

        if not is_valid_table_name(column_name):
            print(
                f'Ошибка: Некорректное имя столбца "{column_name}". '
                "Допустимы только латинские буквы, цифры и подчёркивания. "
                "Имя не может начинаться с цифры."
            )
            return metadata

        if column_name in column_names:
            print(f'Ошибка: Столбец "{column_name}" уже существует или зарезервирован.')
            return metadata

        column_names.add(column_name)
        parsed_columns.append(column)

    parsed_columns.insert(0, ID_COLUMN_DEFINITION)

    metadata[table_name] = parsed_columns

    print(
        f'Таблица "{table_name}" успешно создана со столбцами: '
        f"{', '.join(parsed_columns)}"
    )

    return metadata


@handle_db_errors
@confirm_action("удаление таблицы")
def drop_table(metadata: dict, table_name: str) -> dict:
    """Remove a table definition from metadata after confirmation."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    updated_metadata = metadata.copy()
    del updated_metadata[table_name]
    return updated_metadata


@handle_db_errors
@log_time
def insert(
    metadata: dict,
    table_name: str,
    table_data: list[dict],
    values: list,
) -> list[dict] | None:
    """Validate values and insert a new record into a table."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return None

    columns = metadata[table_name]

    user_columns = [column for column in columns if column.split(":")[0] != ID_COLUMN]

    if len(values) != len(user_columns):
        print("Некорректное количество значений. Попробуйте снова.")
        return None

    record = {}

    for column, value in zip(user_columns, values, strict=True):
        column_name, column_type = column.split(":")

        valid = type(value) is TYPE_MAPPING[column_type]

        if not valid:
            print(f"Некорректное значение: {value}. Попробуйте снова.")
            return None

        record[column_name] = value

    record_id = (
        max(
            (row[ID_COLUMN] for row in table_data),
            default=0,
        )
        + 1
    )

    record = {ID_COLUMN: record_id, **record}

    updated_data = [row.copy() for row in table_data]
    updated_data.append(record)

    print(f'Запись с ID={record_id} успешно добавлена в таблицу "{table_name}".')

    return updated_data


@handle_db_errors
@log_time
def select(
    table_data: list[dict],
    where_clause: dict | None = None,
) -> list[dict]:
    """Return copies of records matching the optional condition."""
    if where_clause is None:
        return [record.copy() for record in table_data]

    return [
        record.copy()
        for record in table_data
        if matches_condition(record, where_clause)
    ]


@handle_db_errors
def update(
    table_data: list[dict],
    set_clause: dict,
    where_clause: dict,
) -> list[dict]:
    """Return updated records without mutating the input records."""
    return [
        {**record, **set_clause}
        if matches_condition(record, where_clause)
        else record.copy()
        for record in table_data
    ]


@handle_db_errors
@confirm_action("удаление записей")
def delete(
    table_data: list[dict],
    where_clause: dict,
) -> list[dict]:
    """Return the records remaining after confirmed deletion."""
    return [
        record.copy()
        for record in table_data
        if not matches_condition(record, where_clause)
    ]
