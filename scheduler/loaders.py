"""
JSON data loader with caching and error handling.

Following Django 5.2 best practices for performance and error handling.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from django.conf import settings

from .models import Position, Worker, Task, Assignment

logger = logging.getLogger(__name__)


class DataLoaderError(Exception):
    """Custom exception for data loading errors."""

    pass


class DataLoader:
    """
    Handles loading and caching of JSON data with proper error handling.
    """

    def __init__(self, base_dir: Optional[Path] = None) -> None:
        """Initialize DataLoader with base directory."""
        self._positions: Optional[List[Position]] = None
        self._workers: Optional[List[Worker]] = None
        self._tasks: Optional[List[Task]] = None
        self._assignments: Optional[List[Assignment]] = None

        # Dictionary lookups for O(1) access
        self._positions_by_id: Optional[Dict[int, Position]] = None
        self._workers_by_id: Optional[Dict[int, Worker]] = None
        self._tasks_by_id: Optional[Dict[int, Task]] = None
        self._assignments_by_task_id: Optional[Dict[int, Assignment]] = None

        self._base_dir = base_dir or settings.BASE_DIR

    def _load_json_file(self, filename: str) -> List[Dict]:
        """
        Load JSON data from file with proper error handling.

        Args:
            filename: Name of the JSON file to load

        Returns:
            List of dictionaries containing the data

        Raises:
            DataLoaderError: If file cannot be loaded or parsed
        """
        file_path = self._base_dir / "data" / filename

        try:
            if not file_path.exists():
                raise DataLoaderError(f"Data file not found: {filename}")

            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, list):
                raise DataLoaderError(f"Expected list in {filename}, got {type(data).__name__}")

            logger.info(f"Successfully loaded {len(data)} items from {filename}")
            return data

        except json.JSONDecodeError as e:
            raise DataLoaderError(f"Invalid JSON in {filename}: {e}") from e
        except OSError as e:
            raise DataLoaderError(f"Cannot read file {filename}: {e}") from e

    def get_positions(self) -> List[Position]:
        """Load and cache positions data."""
        if self._positions is None:
            try:
                data = self._load_json_file("positions.json")
                self._positions = data
                # Create lookup dictionary
                self._positions_by_id = {pos["id"]: pos for pos in data}
                logger.debug(f"Cached {len(self._positions)} positions with lookup dictionary")
            except (KeyError, TypeError) as e:
                raise DataLoaderError(f"Invalid positions data structure: {e}") from e

        return self._positions

    def get_position_by_id(self, position_id: int) -> Optional[Position]:
        """Get position by ID with O(1) lookup."""
        if self._positions_by_id is None:
            self.get_positions()  # This will initialize both list and dict
        return self._positions_by_id.get(position_id)

    def get_workers(self) -> List[Worker]:
        """Load and cache workers data with position names."""
        if self._workers is None:
            try:
                data = self._load_json_file("workers.json")
                self._workers = data
                # Create lookup dictionary
                self._workers_by_id = {worker["id"]: worker for worker in data}
                logger.debug(f"Cached {len(self._workers)} workers with lookup dictionary")
            except (KeyError, TypeError) as e:
                raise DataLoaderError(f"Invalid workers data structure: {e}") from e

        return self._workers

    def get_worker_by_id(self, worker_id: int) -> Optional[Worker]:
        """Get worker by ID with O(1) lookup."""
        if self._workers_by_id is None:
            self.get_workers()  # This will initialize both list and dict
        return self._workers_by_id.get(worker_id)

    def get_tasks(self) -> List[Task]:
        """Load and cache tasks data."""
        if self._tasks is None:
            try:
                data = self._load_json_file("tasks.json")
                self._tasks = data
                # Create lookup dictionary
                self._tasks_by_id = {task["id"]: task for task in data}
                logger.debug(f"Cached {len(self._tasks)} tasks with lookup dictionary")
            except (KeyError, TypeError) as e:
                raise DataLoaderError(f"Invalid tasks data structure: {e}") from e

        return self._tasks

    def get_task_by_id(self, task_id: int) -> Optional[Task]:
        """Get task by ID with O(1) lookup."""
        if self._tasks_by_id is None:
            self.get_tasks()  # This will initialize both list and dict
        return self._tasks_by_id.get(task_id)

    def get_assignments(self) -> List[Assignment]:
        """Load and cache assignments data."""
        if self._assignments is None:
            try:
                data = self._load_json_file("assignments.json")
                self._assignments = data
                # Create lookup dictionary
                self._assignments_by_task_id = {assignment["task_id"]: assignment for assignment in data}
                logger.debug(f"Cached {len(self._assignments)} assignments with lookup dictionary")
            except (KeyError, TypeError) as e:
                raise DataLoaderError(f"Invalid assignments data structure: {e}") from e

        return self._assignments

    def get_assignment_by_task_id(self, task_id: int) -> Optional[Assignment]:
        """Get assignment by task ID with O(1) lookup."""
        if self._assignments_by_task_id is None:
            self.get_assignments()  # This will initialize both list and dict
        return self._assignments_by_task_id.get(task_id)

    def refresh_cache(self) -> None:
        """Clear cached data to force reload on next access."""
        self._positions = None
        self._workers = None
        self._tasks = None
        self._assignments = None
        # Clear lookup dictionaries too
        self._positions_by_id = None
        self._workers_by_id = None
        self._tasks_by_id = None
        self._assignments_by_task_id = None
        logger.info("Data cache cleared")
