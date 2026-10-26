import ast
import re
import shlex

import prompt
from prettytable import PrettyTable

from primitive_db.constants import ID_COLUMN, METADATA_FILE
from primitive_db.core import (
    create_table,
    delete,
    drop_table,
    insert,
    select,
    update,
)
from primitive_db.parser import parse_condition
from primitive_db.utils import (
    load_metadata,
    load_table_data,
    save_metadata,
    save_table_data,
    validate_columns,
)


def print_help() -> None:
    """Display available database commands."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

    print("\n***Операции с данными***")
    print("Функции:")
    print(
        "<command> insert into <имя_таблицы> values "
        "(<значение1>, <значение2>, ...) - создать запись."
    )
    print(
        "<command> select from <имя_таблицы> where "
        "<столбец> = <значение> - прочитать записи по условию."
    )
    print("<command> select from <имя_таблицы> - прочитать все записи.")
    print(
        "<command> update <имя_таблицы> set <столбец> = <новое_значение> "
        "where <столбец_условия> = <значение_условия> - обновить запись."
    )
    print(
        "<command> delete from <имя_таблицы> where "
        "<столбец> = <значение> - удалить запись."
    )
    print("<command> info <имя_таблицы> - вывести информацию о таблице.")

    print("\nОбщие команды:")
    print("<command> exit - выход из программы")
    print("<command> help - справочная информация\n")


def run() -> None:
    """Run the database command-line interface."""
    print_help()

    while True:
        metadata = load_metadata(METADATA_FILE)
        user_input = prompt.string("Введите команду: ")

        try:
            args = shlex.split(user_input)
        except ValueError:
            print(f"Некорректное значение: {user_input}. Попробуйте снова.")
            continue

        if not args:
            continue

        command = args[0]

        if command == "exit":
            break

        elif command == "help":
            print_help()

        elif command == "list_tables":
            if metadata:
                for table_name in metadata:
                    print(f"- {table_name}")
            else:
                print("Таблиц пока нет.")

        elif command == "create_table":
            if len(args) < 3:
                print(
                    "Некорректное значение: недостаточно аргументов. Попробуйте снова."
                )
                continue

            table_name = args[1]
            columns = args[2:]

            if table_name not in metadata:
                metadata = create_table(metadata, table_name, columns)

                if table_name in metadata:
                    save_metadata(METADATA_FILE, metadata)
            else:
                create_table(metadata, table_name, columns)

        elif command == "info":
            if len(args) != 2:
                print("Некорректное значение: аргументы команды. Попробуйте снова.")
                continue

            table_name = args[1]

            if table_name not in metadata:
                print(f'Ошибка: Таблица "{table_name}" не существует.')
                continue

            columns = metadata[table_name]
            table_data = load_table_data(table_name)

            print(f"Таблица: {table_name}")
            print(f"Столбцы: {', '.join(columns)}")
            print(f"Количество записей: {len(table_data)}")

        elif command == "delete":
            try:
                if len(args) < 7 or args[1] != "from" or args[3] != "where":
                    raise ValueError("Некорректный синтаксис команды delete.")

                table_name = args[2]

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                match = re.match(
                    r"^\s*delete\s+from\s+\S+\s+where\s+(.+)$",
                    user_input,
                )

                if match is None:
                    raise ValueError("Некорректное условие WHERE.")

                where_clause = parse_condition(match.group(1).strip())

                validate_columns(metadata[table_name], where_clause)

                table_data = load_table_data(table_name)
                matching_records = select(table_data, where_clause)

                if not matching_records:
                    print("Записи по указанному условию не найдены.")
                    continue

                updated_data = delete(table_data, where_clause)

                if updated_data is not None:
                    save_table_data(table_name, updated_data)

            except (ValueError, KeyError) as error:
                print(f"Ошибка: {error}")

        elif command == "update":
            try:
                if len(args) < 10 or args[2] != "set":
                    raise ValueError("Некорректный синтаксис команды update.")

                table_name = args[1]

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                match = re.match(
                    r"""^\s*update\s+\S+\s+set\s+((?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*'|[^"'])*?)\s+where\s+(.+)$""",
                    user_input,
                )

                if match is None:
                    raise ValueError("Отсутствует или некорректно указано WHERE.")

                set_clause = parse_condition(match.group(1).strip())
                where_clause = parse_condition(match.group(2).strip())

                validate_columns(metadata[table_name], set_clause)
                validate_columns(metadata[table_name], where_clause)

                if ID_COLUMN in set_clause:
                    raise ValueError("Изменение столбца ID запрещено.")

                table_data = load_table_data(table_name)

                matching_ids = [
                    record[ID_COLUMN] for record in select(table_data, where_clause)
                ]

                if not matching_ids:
                    print("Записи по указанному условию не найдены.")
                    continue

                updated_data = update(table_data, set_clause, where_clause)
                save_table_data(table_name, updated_data)

            except (ValueError, KeyError) as error:
                print(f"Ошибка: {error}")

        elif command == "select":
            try:
                if len(args) < 3 or args[1] != "from":
                    raise ValueError("Некорректный синтаксис команды select.")

                table_name = args[2]

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

                where_clause = None

                if len(args) > 3:
                    if len(args) < 7 or args[3] != "where":
                        raise ValueError("Некорректное условие WHERE.")

                    match = re.match(
                        r"^\s*select\s+from\s+\S+\s+where\s+(.+)$",
                        user_input,
                    )

                    if match is None:
                        raise ValueError("Некорректное условие WHERE.")

                    where_clause = parse_condition(match.group(1).strip())

                if where_clause is not None:
                    validate_columns(metadata[table_name], where_clause)

                table_data = load_table_data(table_name)
                selected_data = select(table_data, where_clause)

                columns = [column.split(":")[0] for column in metadata[table_name]]

                table = PrettyTable()
                table.field_names = columns

                for record in selected_data:
                    table.add_row([record[column] for column in columns])

                print(table)

            except (ValueError, KeyError) as error:
                print(f"Ошибка: {error}")

        elif command == "insert":
            try:
                if len(args) < 5 or args[1] != "into" or args[3] != "values":
                    raise ValueError("Некорректный синтаксис команды insert.")

                table_name = args[2]

                if table_name not in metadata:
                    print(f'Ошибка: Таблица "{table_name}" не существует.')
                    continue

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

                values = list(ast.literal_eval(f"[{values_text}]"))

                result = insert(metadata, table_name, values)

                if result is not None:
                    save_table_data(table_name, result)

            except (ValueError, SyntaxError, StopIteration) as error:
                print(f"Ошибка: {error}")

        elif command == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: аргументы команды. Попробуйте снова.")
                continue

            table_name = args[1]

            if table_name in metadata:
                updated_metadata = drop_table(metadata, table_name)

                if updated_metadata is not None:
                    save_metadata(METADATA_FILE, updated_metadata)
            else:
                print(f'Ошибка: Таблица "{table_name}" не существует.')

        else:
            print(f"Функции {command} нет. Попробуйте снова.")
