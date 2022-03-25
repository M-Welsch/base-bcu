from typing import Callable


def derive_mock_string(func: Callable) -> str:
    return f"{func.__module__}.{func.__qualname__}"
