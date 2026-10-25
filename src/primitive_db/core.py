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
        f'{", ".join(parsed_columns)}'
    )

    return metadata

def drop_table(metadata: dict, table_name: str) -> dict:
    """Delete a table from metadata if it exists."""
    if table_name not in metadata:
        print(f'Ошибка: Таблица "{table_name}" не существует.')
        return metadata

    del metadata[table_name]

    print(f'Таблица "{table_name}" успешно удалена.')

    return metadata