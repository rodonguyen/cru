import logging
from collections import defaultdict
from datetime import datetime
from typing import Dict, List
from django.utils.dateformat import format as date_format

from .loaders import DataLoader
from .constants import EMPTY_POSITION_ID, EMPTY_POSITION_NAME

logger = logging.getLogger(__name__)


class ScheduleProcessorError(Exception):
    """Custom exception for schedule processing errors."""

    pass


class ScheduleDataProcessor:
    """Processes schedule data into table format optimized for frontend display."""

    def __init__(self, data_loader: DataLoader):
        """Initialize processor with data loader."""
        self.data_loader = data_loader

    def _format_date(self, date_str: str) -> str:
        """
        Format date string to 'DD MMM YY' format.

        Args:
            date_str: Date in YYYY-MM-DD format

        Returns:
            Formatted date string like '11 Jan 25'
        """
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            return date_format(date_obj, "d M y")
        except ValueError as e:
            raise ScheduleProcessorError(f"Invalid date format '{date_str}': {e}") from e

    def process_schedule_data(self) -> Dict:
        """
        Process all data into schedule table format.

        Returns:
            Dictionary with 'columns' and 'rows' keys for frontend consumption
        """
        try:
            logger.info("Starting schedule data processing")

            assignments = self.data_loader.get_assignments()

            dates = set()
            worker_date = defaultdict(dict)  # 2D map to store work duration for each worker on each date
            position_worker = defaultdict(set)  # Position to workers existing in the assignments
            position_date = defaultdict(dict)  # 2D map to store work duration for each position on each date

            for assignment in assignments:
                date = self.data_loader.get_task_by_id(assignment["task_id"])["date"]
                worker_id = assignment["worker_id"]

                # Get task duration
                task = self.data_loader.get_task_by_id(assignment["task_id"])
                duration = task["duration"]

                # Handle null position_id - use special constant
                position_id = task["position_id"] if task["position_id"] is not None else EMPTY_POSITION_ID

                # Add duration to worker_date
                worker_date[worker_id][date] = worker_date[worker_id].get(date, 0) + duration

                # Add date to dates set
                dates.add(date)

                # Add worker to position_worker
                position_worker[position_id].add(worker_id)

                # Add duration to position_date
                position_date[position_id][date] = position_date[position_id].get(date, 0) + duration

            schedule = []
            dates = sorted(dates)

            # Sort positions to show empty position last
            sorted_positions = sorted(position_worker.keys(), key=lambda x: (x == EMPTY_POSITION_ID, x))

            for position_id in sorted_positions:
                # Handle position name for empty position
                if position_id == EMPTY_POSITION_ID:
                    position_name = EMPTY_POSITION_NAME
                else:
                    position_name = self.data_loader.get_position_by_id(position_id)["name"]

                position_row = [position_name] + [position_date[position_id].get(date, 0) for date in dates]
                schedule.append(position_row)

                # Insert worker rows of this position under the position row
                for worker_id in position_worker[position_id]:
                    worker_name = self.data_loader.get_worker_by_id(worker_id)["name"]
                    worker_row = [worker_name] + [worker_date[worker_id].get(date, 0) for date in dates]
                    schedule.append(worker_row)

            formatted_dates = [self._format_date(date) for date in dates]
            columns = ["Name"] + formatted_dates if len(schedule) > 0 else []
            return {"columns": columns, "rows": schedule}

        except Exception as e:
            logger.error(f"Schedule processing failed: {e}")
            raise ScheduleProcessorError(f"Failed to process schedule data: {e}") from e
