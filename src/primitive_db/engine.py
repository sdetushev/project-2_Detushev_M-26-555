import shlex

import prompt

from primitive_db.core import create_table, drop_table
from primitive_db.utils import load_metadata, save_metadata

METADATA_FILE = "db_meta.json"


def print_help() -> None:
    """Display available database commands."""
    print("\n***Процесс работы с таблицей***")
    print("Функции:")
    print("<command> create_table <имя_таблицы> <столбец1:тип> .. - создать таблицу")
    print("<command> list_tables - показать список всех таблиц")
    print("<command> drop_table <имя_таблицы> - удалить таблицу")

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
                print("Некорректное значение: недостаточно аргументов."
                      " Попробуйте снова.")
                continue

            table_name = args[1]
            columns = args[2:]

            if table_name not in metadata:
                metadata = create_table(metadata, table_name, columns)

                if table_name in metadata:
                    save_metadata(METADATA_FILE, metadata)
            else:
                create_table(metadata, table_name, columns)

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