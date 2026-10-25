import ast
import re
import shlex

import prompt
from prettytable import PrettyTable

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
)

METADATA_FILE = "db_meta.json"


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
            quoted_args = shlex.split(user_input, posix=False)
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

                where_clause = parse_condition(" ".join(quoted_args[4:]))

                column_types = dict(
                    column.split(":") for column in metadata[table_name]
                )

                for column, value in where_clause.items():
                    if column not in column_types:
                        raise ValueError(f"Столбец '{column}' не существует.")

                    expected_type = {
                        "int": int,
                        "str": str,
                        "bool": bool,
                    }[column_types[column]]

                    if type(value) is not expected_type:
                        raise ValueError(
                            f"Некорректный тип значения для столбца '{column}'."
                        )

                table_data = load_table_data(table_name)
                matching_records = select(table_data, where_clause)

                if not matching_records:
                    print("Записи по указанному условию не найдены.")
                    continue

                updated_data = delete(table_data, where_clause)
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

                if args.count("where") != 1:
                    raise ValueError("Отсутствует или некорректно указано WHERE.")

                where_index = args.index("where")

                set_clause = parse_condition(" ".join(quoted_args[3:where_index]))
                where_clause = parse_condition(" ".join(quoted_args[where_index + 1 :]))

                column_types = dict(
                    column.split(":") for column in metadata[table_name]
                )

                for column, value in {**set_clause, **where_clause}.items():
                    if column not in column_types:
                        raise ValueError(f"Столбец '{column}' не существует.")

                    expected_type = {
                        "int": int,
                        "str": str,
                        "bool": bool,
                    }[column_types[column]]

                    if type(value) is not expected_type:
                        raise ValueError(
                            f"Некорректный тип значения для столбца '{column}'."
                        )

                if "ID" in set_clause:
                    raise ValueError("Изменение столбца ID запрещено.")

                table_data = load_table_data(table_name)

                matching_ids = [
                    record["ID"] for record in select(table_data, where_clause)
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

                    where_clause = parse_condition(" ".join(quoted_args[4:]))

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

                values_text = user_input.split("values", maxsplit=1)[1].strip()

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

            except (ValueError, StopIteration) as error:
                print(f"Ошибка: {error}")

        elif command == "drop_table":
            if len(args) != 2:
                print("Некорректное значение: аргументы команды. Попробуйте снова.")
                continue

            table_name = args[1]

            if table_name in metadata:
                metadata = drop_table(metadata, table_name)
                save_metadata(METADATA_FILE, metadata)
            else:
                drop_table(metadata, table_name)

        else:
            print(f"Функции {command} нет. Попробуйте снова.")
