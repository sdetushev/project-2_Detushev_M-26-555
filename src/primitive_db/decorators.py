import time
from functools import wraps
from typing import Any, Callable


def handle_db_errors(func: Callable) -> Callable:
    """Handle common database errors raised by a function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Execute a function and handle database errors."""
        try:
            return func(*args, **kwargs)
        except FileNotFoundError:
            print("Ошибка: Файл данных не найден.")
        except KeyError as error:
            print(f"Ошибка: Таблица или столбец {error} не найден.")
        except ValueError as error:
            print(f"Ошибка валидации: {error}")

    return wrapper


def confirm_action(action_name: str) -> Callable:
    """Request user confirmation before executing an action."""

    def decorator(func: Callable) -> Callable:
        """Wrap a function with a confirmation prompt."""

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            """Execute the function only after confirmation."""
            answer = input(f'Вы уверены, что хотите выполнить "{action_name}"? [y/n]: ')

            if answer.strip().lower() != "y":
                print("Операция отменена.")
                return None

            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_time(func: Callable) -> Callable:
    """Measure and display the execution time of a function."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        """Execute a function and log its execution time."""
        start_time = time.monotonic()

        try:
            return func(*args, **kwargs)
        finally:
            elapsed_time = time.monotonic() - start_time
            print(f"Функция {func.__name__} выполнилась за {elapsed_time:.3f} секунд.")

    return wrapper


def create_cacher() -> Callable:
    """Create a function that caches results by key."""
    cache = {}

    def cache_result(key: str, value_func: Callable) -> Any:
        """Return a cached result or calculate and store it."""
        if key not in cache:
            cache[key] = value_func()

        return cache[key]

    def clear_cache() -> None:
        """Remove all cached results."""
        cache.clear()

    cache_result.clear_cache = clear_cache

    return cache_result
