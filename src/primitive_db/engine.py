import prompt


def welcome() -> None:
    """Display the welcome message and process user commands."""
    print("Первая попытка запустить проект!\n")
    print("***")
    print("<command> exit - выйти из программы")
    print("<command> help - справочная информация")

    while True:
        command = prompt.string("Введите команду: ")

        if command == "exit":
            break
        elif command == "help":
            print()
            print("<command> exit - выйти из программы")
            print("<command> help - справочная информация")