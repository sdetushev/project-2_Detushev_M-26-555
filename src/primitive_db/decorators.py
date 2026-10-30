import time


def handle_db_errors(func):
    """Handle common database errors raised by a function."""

    def wrapper(*args, **kwargs):
        """Execute a function and handle database errors."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def confirm_action(action_name: str):
    """Request user confirmation before executing an action."""

    def decorator(func):
        """Wrap a function with a confirmation prompt."""

        def wrapper(*args, **kwargs):
            """Execute the function only after confirmation."""
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__

        return wrapper

    return decorator


def log_time(func):
    """Measure and display the execution time of a function."""

    def wrapper(*args, **kwargs):
        """Execute a function and log its execution time."""
        start_time = time.monotonic()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.monotonic() - start_time
            print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд.")

    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__

    return wrapper


def create_cacher():
    """Create a function that caches results by key."""
    cache = {}

    def cache_result(key: str, value_func):
        """Return a copy of the cached result or calculate and store it."""
        if key not in cache:
            cache[key] = value_func()

        return [record.copy() for record in cache[key]]

    return cache_result
