import logging
import time
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

logger = logging.getLogger(__name__)


# Define generic type variables for return type and parameters
R = TypeVar("R")
P = ParamSpec("P")


def time_execution_sync(
    additional_text: str = "",
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        @wraps(func)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{additional_text} Execution time: {execution_time:.2f} seconds"
            )
            return result

        return wrapper

    return decorator


def time_execution_async(
    additional_text: str = "",
) -> Callable[
    [Callable[P, Coroutine[Any, Any, R]]], Callable[P, Coroutine[Any, Any, R]]
]:
    def decorator(
        func: Callable[P, Coroutine[Any, Any, R]],
    ) -> Callable[P, Coroutine[Any, Any, R]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            start_time = time.time()
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(
                f"{additional_text} Execution time: {execution_time:.2f} seconds"
            )
            return result

        return wrapper

    return decorator


def singleton(cls):
    instance = [None]

    def wrapper(*args, **kwargs):
        if instance[0] is None:
            instance[0] = cls(*args, **kwargs)
        return instance[0]

    return wrapper


class LatencyAnalyzer:
    def __init__(self):
        self.records = []

    def record(
        self,
        name: str,
        start_time: float,
        end_time: float,
        step_number: int = None,
        additional_info: dict = None,
    ):
        duration = end_time - start_time
        record = {
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "step_number": step_number,
            **(additional_info or {}),
        }
        self.records.append(record)

    def write_to_csv(self, file_path: str):
        import csv
        import os

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", newline="") as csvfile:
            if not self.records:
                return
            # Collect all unique fieldnames from all records
            fieldnames = set()
            for record in self.records:
                fieldnames.update(record.keys())
            fieldnames = sorted(list(fieldnames))  # Sort for consistent order
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for record in self.records:
                writer.writerow(record)
