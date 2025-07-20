import os
import tempfile
import json
from pathlib import Path
from django.test import TestCase
from unittest.mock import patch

from scheduler.loaders import DataLoader, DataLoaderError
from scheduler.processors import ScheduleDataProcessor, ScheduleProcessorError


class ScheduleDataProcessorTestCase(TestCase):
    """Test cases for ScheduleDataProcessor using Django's testing framework."""

    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create temporary directory for test data
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.test_dir) / "data"
        self.test_data_dir.mkdir()

        # Create simple test data
        self.positions_data = [{"id": 1, "name": "Manager"}, {"id": 2, "name": "Developer"}]

        self.workers_data = [
            {"id": 1, "name": "Alice", "position_id": 1},
            {"id": 2, "name": "Bob", "position_id": 2},
            {"id": 3, "name": "Carol", "position_id": 2},
        ]

        self.tasks_data = [
            {"id": 1, "position_id": 1, "duration": 4, "date": "2025-01-15"},
            {"id": 2, "position_id": 2, "duration": 6, "date": "2025-01-15"},
            {"id": 3, "position_id": 2, "duration": 3, "date": "2025-01-16"},
        ]

        self.assignments_data = [
            {"task_id": 1, "worker_id": 1},
            {"task_id": 2, "worker_id": 2},
            {"task_id": 3, "worker_id": 3},
        ]

        # Write test data files
        self._write_test_files()

        # Create DataLoader and processor
        self.loader = DataLoader(base_dir=Path(self.test_dir))
        self.processor = ScheduleDataProcessor(self.loader)

    def tearDown(self):
        """Clean up after each test method."""
        import shutil

        shutil.rmtree(self.test_dir)

    def _write_test_files(self):
        """Write test data to JSON files."""
        files_data = {
            "positions.json": self.positions_data,
            "workers.json": self.workers_data,
            "tasks.json": self.tasks_data,
            "assignments.json": self.assignments_data,
        }

        for filename, data in files_data.items():
            file_path = self.test_data_dir / filename
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

    def test_process_schedule_data__basic_structure(self):
        result = self.processor.process_schedule_data()

        # Check basic structure
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertIsInstance(result["columns"], list)
        self.assertIsInstance(result["rows"], list)

    def test_process_schedule_data__columns(self):
        result = self.processor.process_schedule_data()
        columns = result["columns"]

        # Should have Name column plus date columns
        self.assertEqual(columns[0], "Name")
        self.assertIn("15 Jan 25", columns)
        self.assertIn("16 Jan 25", columns)
        self.assertEqual(len(columns), 3)  # Name + 2 dates

    def test_process_schedule_data__rows_structure(self):
        """Test that rows follow position->workers hierarchy."""
        result = self.processor.process_schedule_data()
        rows = result["rows"]

        # Should have position rows followed by worker rows
        # Expected: Manager, Alice, Developer, Bob, Carol
        self.assertEqual(len(rows), 5)

        # Check position rows (should be first in each group)
        manager_row = rows[0]
        developer_row = rows[2]

        self.assertEqual(manager_row[0], "Manager")
        self.assertEqual(developer_row[0], "Developer")

        # Check worker rows
        alice_row = rows[1]
        bob_row = rows[3]
        carol_row = rows[4]

        self.assertEqual(alice_row[0], "Alice")
        self.assertEqual(bob_row[0], "Bob")
        self.assertEqual(carol_row[0], "Carol")

    def test_process_schedule_data__duration_aggregation(self):
        """Test that durations are correctly aggregated."""
        result = self.processor.process_schedule_data()
        rows = result["rows"]

        # Manager row should have Alice's hours: [4, 0] for dates 15th, 16th
        manager_row = rows[0]
        self.assertEqual(manager_row[1], 4)  # 15 Jan
        self.assertEqual(manager_row[2], 0)  # 16 Jan

        # Alice row should match manager (she's the only manager)
        alice_row = rows[1]
        self.assertEqual(alice_row[1], 4)  # 15 Jan
        self.assertEqual(alice_row[2], 0)  # 16 Jan

        # Developer row should sum Bob + Carol: [6, 3]
        developer_row = rows[2]
        self.assertEqual(developer_row[1], 6)  # 15 Jan (Bob's 6 hours)
        self.assertEqual(developer_row[2], 3)  # 16 Jan (Carol's 3 hours)

        # Bob row: [6, 0]
        bob_row = rows[3]
        self.assertEqual(bob_row[1], 6)  # 15 Jan
        self.assertEqual(bob_row[2], 0)  # 16 Jan

        # Carol row: [0, 3]
        carol_row = rows[4]
        self.assertEqual(carol_row[1], 0)  # 15 Jan
        self.assertEqual(carol_row[2], 3)  # 16 Jan

    def test_process_schedule_data__with_multiple_tasks_same_day(self):
        """Test aggregation when worker has multiple tasks on same day."""
        # Add another task for Bob on the same day
        additional_task = {"id": 4, "position_id": 2, "duration": 2, "date": "2025-01-15"}
        additional_assignment = {"task_id": 4, "worker_id": 2}

        self.tasks_data.append(additional_task)
        self.assignments_data.append(additional_assignment)
        self._write_test_files()

        # Create new loader/processor to pick up updated data
        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)

        result = processor.process_schedule_data()
        rows = result["rows"]

        # Bob should now have 6 + 2 = 8 hours on 15 Jan
        bob_row = rows[3]
        self.assertEqual(bob_row[1], 8)  # 15 Jan (6 + 2)

        # Developer total should also increase
        developer_row = rows[2]
        self.assertEqual(developer_row[1], 8)  # 15 Jan (Bob's 8 + Carol's 0)

    def test_process_schedule_data__empty_assignments(self):
        self.assignments_data = []
        self._write_test_files()

        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)

        result = processor.process_schedule_data()

        # Should return structure with no rows
        self.assertEqual(len(result["rows"]), 0)
        self.assertEqual(len(result["columns"]), 0)

    def test_process_schedule_data__date_formatting(self):
        result = self.processor.process_schedule_data()
        columns = result["columns"]

        # Check date format (DD MMM YY)
        self.assertIn("15 Jan 25", columns)
        self.assertIn("16 Jan 25", columns)

    def test_process_schedule_data__with_data_loader_error(self):
        # Create processor with invalid data directory
        invalid_loader = DataLoader(base_dir=Path("/nonexistent"))
        invalid_processor = ScheduleDataProcessor(invalid_loader)

        with self.assertRaises(ScheduleProcessorError):
            invalid_processor.process_schedule_data()

    def test_process_schedule_data__with_invalid_date(self):
        # Add task with invalid date
        self.tasks_data[0]["date"] = "invalid-date"
        self._write_test_files()

        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)

        with self.assertRaises(ScheduleProcessorError):
            processor.process_schedule_data()

    def test_date_format_method(self):
        # Test valid date
        formatted = self.processor._format_date("2025-01-15")
        self.assertEqual(formatted, "15 Jan 25")

        # Test invalid date
        with self.assertRaises(ScheduleProcessorError):
            self.processor._format_date("invalid-date")

    def test_null_position_id_handling(self):
        """Test that null position_id values are handled correctly."""
        # Add task with null position_id
        null_position_task = {"id": 999, "position_id": None, "duration": 5, "date": "2025-01-15"}

        # Add worker with null position_id
        null_position_worker = {"id": 999, "name": "Unassigned Worker", "position_id": None}

        # Add assignment for null position task
        null_assignment = {"task_id": 999, "worker_id": 999}

        # Update test data
        self.tasks_data.append(null_position_task)
        self.workers_data.append(null_position_worker)
        self.assignments_data.append(null_assignment)
        self._write_test_files()

        # Process schedule data
        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)
        result = processor.process_schedule_data()

        # Verify empty position is included
        position_names = [
            row[0] for row in result["rows"] if row[0] in ["Supervisor", "Welder", "Fitter", "Empty Position"]
        ]
        self.assertIn("Empty Position", position_names)

        # Verify empty position is last (sorted)
        last_position_idx = max(
            [
                i
                for i, row in enumerate(result["rows"])
                if row[0] in ["Supervisor", "Welder", "Fitter", "Empty Position"]
            ]
        )
        self.assertEqual(result["rows"][last_position_idx][0], "Empty Position")

        # Verify worker appears under empty position
        empty_position_idx = next(i for i, row in enumerate(result["rows"]) if row[0] == "Empty Position")
        worker_under_empty = result["rows"][empty_position_idx + 1]
        self.assertEqual(worker_under_empty[0], "Unassigned Worker")

        # Verify duration is calculated correctly for empty position
        jan_15_col_idx = result["columns"].index("15 Jan 25")
        empty_position_duration = result["rows"][empty_position_idx][jan_15_col_idx]
        worker_duration = worker_under_empty[jan_15_col_idx]
        self.assertEqual(empty_position_duration, 5)
        self.assertEqual(worker_duration, 5)
