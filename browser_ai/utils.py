import io
import logging
import time
import uuid
from functools import wraps
from typing import Any, Callable, Coroutine, ParamSpec, TypeVar

import aiofiles

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
    _task_id_map = {}  # Class variable to map task names to UUID IDs

    def __init__(self):
        self.records = []
        self.run_id = str(uuid.uuid4())
        self.run_timestamp = time.time()

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
            "run_id": self.run_id,
            "run_timestamp": self.run_timestamp,
            "name": name,
            "start_time": start_time,
            "end_time": end_time,
            "duration": duration,
            "step_number": step_number,
            **(additional_info or {}),
        }
        # Assign task_id if task is present
        if additional_info and "task" in additional_info:
            task = additional_info["task"]
            if task not in self._task_id_map:
                self._task_id_map[task] = str(uuid.uuid4())
            record["task_id"] = self._task_id_map[task]
        self.records.append(record)

    async def write_to_csv(self, file_path: str):
        import csv
        import os

        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        if not self.records:
            return

        # Read existing records if file exists
        existing_records = []
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", newline="") as existing_file:
                    reader = csv.DictReader(existing_file)
                    existing_records = list(reader)
            except (IOError, csv.Error):
                pass  # If can't read, start fresh

        # Combine existing and new records
        all_records = existing_records + self.records

        # Clean records to remove None keys
        cleaned_records = []
        for record in all_records:
            cleaned_record = {k: v for k, v in record.items() if k is not None}
            cleaned_records.append(cleaned_record)

        # Collect all unique fieldnames from cleaned records
        fieldnames = set()
        for record in cleaned_records:
            fieldnames.update(record.keys())
        fieldnames = sorted(list(fieldnames))  # Sort for consistent order

        # Write all records with merged header
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for record in cleaned_records:
            writer.writerow(record)
        csv_content = output.getvalue()
        output.close()

        async with aiofiles.open(file_path, "w", newline="") as f:
            await f.write(csv_content)
