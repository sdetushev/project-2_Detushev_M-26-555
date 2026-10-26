import json
from pathlib import Path

from primitive_db.constants import DATA_DIR, TYPE_MAPPING


def load_metadata(filepath: str) -> dict:
    """Load metadata from a JSON file or return an empty dictionary."""
    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def save_metadata(filepath: str, data: dict) -> None:
    """Save metadata to a JSON file."""
    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def load_table_data(table_name: str) -> list[dict]:
    """Load table records from a JSON file."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"

    try:
        with open(filepath, encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def save_table_data(table_name: str, data: list[dict]) -> None:
    """Save table records to a JSON file."""
    filepath = Path(DATA_DIR) / f"{table_name}.json"
    filepath.parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


def validate_columns(
    columns: list[str],
    values: dict,
) -> None:
    """Validate column names and value types against the table schema."""
    column_types = dict(column.split(":") for column in columns)

    for column, value in values.items():
        if column not in column_types:
            raise ValueError(f"Столбец '{column}' не существует.")

        expected_type = TYPE_MAPPING[column_types[column]]

        if type(value) is not expected_type:
            raise ValueError(f"Некорректный тип значения для столбца '{column}'.")
