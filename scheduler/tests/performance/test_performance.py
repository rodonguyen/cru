import json
import time
import tempfile
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from dataclasses import dataclass
from django.test import TestCase
from unittest.mock import patch
import psutil
import os

from scheduler.loaders import DataLoader
from scheduler.processors import ScheduleDataProcessor
from scheduler.tests.performance.performance_config import PERFORMANCE_THRESHOLDS


@dataclass
class PerformanceMetrics:
    """Container for performance measurement results."""

    processing_time: float
    memory_usage_mb: float
    data_scale: Dict[str, int]
    peak_memory_mb: float


class LargeDataGenerator:
    """Generates large-scale test data for performance testing."""

    def __init__(self, base_scale_factor: int = 1000):
        self.scale_factor = base_scale_factor
        self.positions_count = 3 * base_scale_factor
        self.workers_count = 10 * base_scale_factor
        self.tasks_count = 50 * base_scale_factor
        self.assignments_count = 50 * base_scale_factor

    def generate_positions(self) -> List[Dict]:
        """Generate positions data."""
        base_positions = ["Supervisor", "Welder", "Fitter", "Engineer", "Technician", "Operator"]
        positions = []

        for i in range(self.positions_count):
            positions.append({"id": i + 1, "name": f"{random.choice(base_positions)} {i // len(base_positions) + 1}"})
        return positions

    def generate_workers(self, positions: List[Dict]) -> List[Dict]:
        """Generate workers data with realistic distribution."""
        first_names = ["John", "Jane", "Mike", "Sarah", "David", "Lisa", "Chris", "Anna", "Tom", "Emma"]
        last_names = [
            "Smith",
            "Johnson",
            "Williams",
            "Brown",
            "Jones",
            "Garcia",
            "Miller",
            "Davis",
            "Rodriguez",
            "Martinez",
        ]

        workers = []
        for i in range(self.workers_count):
            workers.append(
                {
                    "id": i + 1,
                    "name": f"{random.choice(first_names)} {random.choice(last_names)}",
                    "position_id": random.choice(positions)["id"],
                }
            )
        return workers

    def generate_tasks(self, positions: List[Dict], date_range_days: int = 30) -> List[Dict]:
        """Generate tasks data across a date range."""
        start_date = datetime(2025, 1, 1).date()
        tasks = []

        for i in range(self.tasks_count):
            random_days = random.randint(0, date_range_days - 1)
            task_date = start_date + timedelta(days=random_days)

            tasks.append(
                {
                    "id": i + 1,
                    "position_id": random.choice(positions)["id"],
                    "duration": random.randint(1, 8),  # 1-8 hours
                    "date": task_date.strftime("%Y-%m-%d"),
                }
            )
        return tasks

    def generate_assignments(self, tasks: List[Dict], workers: List[Dict]) -> List[Dict]:
        """Generate assignments ensuring referential integrity."""
        assignments = []

        # Create position_id to worker mapping for efficiency
        position_workers = {}
        for worker in workers:
            pos_id = worker["position_id"]
            if pos_id not in position_workers:
                position_workers[pos_id] = []
            position_workers[pos_id].append(worker["id"])

        for i in range(self.assignments_count):
            if i < len(tasks):
                task = tasks[i]
                # Assign to a worker with matching position
                matching_workers = position_workers.get(task["position_id"], [])
                if matching_workers:
                    assignments.append({"task_id": task["id"], "worker_id": random.choice(matching_workers)})

        return assignments

    def generate_all_data(self) -> Tuple[List, List, List, List]:
        """Generate complete dataset."""
        print(f"Generating data with scale factor {self.scale_factor}:")
        print(f"  - Positions: {self.positions_count}")
        print(f"  - Workers: {self.workers_count}")
        print(f"  - Tasks: {self.tasks_count}")
        print(f"  - Assignments: {self.assignments_count}")

        positions = self.generate_positions()
        workers = self.generate_workers(positions)
        tasks = self.generate_tasks(positions)
        assignments = self.generate_assignments(tasks, workers)

        return positions, workers, tasks, assignments


class PerformanceTestCase(TestCase):
    """Performance tests for ScheduleDataProcessor with large datasets."""

    def setUp(self):
        """Set up performance testing environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_data_dir = Path(self.test_dir) / "data"
        self.test_data_dir.mkdir()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.test_dir)

    def _write_data_files(self, positions: List, workers: List, tasks: List, assignments: List):
        """Write generated data to JSON files."""
        files_data = {
            "positions.json": positions,
            "workers.json": workers,
            "tasks.json": tasks,
            "assignments.json": assignments,
        }

        for filename, data in files_data.items():
            file_path = self.test_data_dir / filename
            with open(file_path, "w") as f:
                json.dump(data, f)

    def _measure_performance(self, scale_factor: int) -> PerformanceMetrics:
        """Measure processing performance for given scale."""
        # Generate data
        generator = LargeDataGenerator(scale_factor)
        positions, workers, tasks, assignments = generator.generate_all_data()

        # Write data files
        self._write_data_files(positions, workers, tasks, assignments)

        # Create processor
        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)

        # Measure initial memory
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Measure processing time
        start_time = time.time()
        result = processor.process_schedule_data()
        end_time = time.time()

        # Measure peak memory
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB

        processing_time = end_time - start_time
        memory_usage = peak_memory - initial_memory

        return PerformanceMetrics(
            processing_time=processing_time,
            memory_usage_mb=memory_usage,
            peak_memory_mb=peak_memory,
            data_scale={
                "positions": len(positions),
                "workers": len(workers),
                "tasks": len(tasks),
                "assignments": len(assignments),
            },
        )

    def test_performance_baseline(self):
        """Test performance with baseline (current) dataset size."""
        metrics = self._measure_performance(scale_factor=1)

        print(f"\nBaseline Performance:")
        print(f"  Processing time: {metrics.processing_time:.3f} seconds")
        print(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
        print(f"  Data scale: {metrics.data_scale}")

        # Baseline should be fast
        self.assertLess(
            metrics.processing_time,
            PERFORMANCE_THRESHOLDS[1].max_processing_time_seconds,
            "Baseline should process under the threshold",
        )
        self.assertLess(
            metrics.memory_usage_mb,
            PERFORMANCE_THRESHOLDS[1].max_memory_usage_mb,
            "Baseline should use less than the threshold",
        )

    def test_performance_1000x_scale(self):
        """Test performance with 1000x dataset size"""
        metrics = self._measure_performance(scale_factor=1000)

        print(f"\n1000x Scale Performance:")
        print(f"  Processing time: {metrics.processing_time:.3f} seconds")
        print(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
        print(f"  Peak memory: {metrics.peak_memory_mb:.1f} MB")
        print(f"  Data scale: {metrics.data_scale}")

        # Performance thresholds for 1000x scale
        self.assertLess(
            metrics.processing_time,
            PERFORMANCE_THRESHOLDS[1000].max_processing_time_seconds,
            "1000x scale should process under the threshold",
        )
        self.assertLess(
            metrics.memory_usage_mb,
            PERFORMANCE_THRESHOLDS[1000].max_memory_usage_mb,
            "1000x scale should use less than the threshold",
        )

        # Verify data integrity
        loader = DataLoader(base_dir=Path(self.test_dir))
        processor = ScheduleDataProcessor(loader)
        result = processor.process_schedule_data()

        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertGreater(len(result["rows"]), 0, "Should produce output rows")

    def test_performance_10000x_scale(self):
        """Test performance with 10000x dataset size."""
        metrics = self._measure_performance(scale_factor=10000)

        print(f"\n10000x Scale Performance:")
        print(f"  Processing time: {metrics.processing_time:.3f} seconds")
        print(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
        print(f"  Data scale: {metrics.data_scale}")

        # Should be acceptable for batch processing
        self.assertLess(
            metrics.processing_time,
            PERFORMANCE_THRESHOLDS[10000].max_processing_time_seconds,
            "10000x scale should process under the threshold",
        )
        self.assertLess(
            metrics.memory_usage_mb,
            PERFORMANCE_THRESHOLDS[10000].max_memory_usage_mb,
            "10000x scale should use less than the threshold",
        )

    def test_performance_100000x_scale(self):
        """Test performance with 100000x dataset size."""
        metrics = self._measure_performance(scale_factor=100000)

        print(f"\n100000x Scale Performance:")
        print(f"  Processing time: {metrics.processing_time:.3f} seconds")
        print(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
        print(f"  Data scale: {metrics.data_scale}")

        # Should be acceptable for batch processing
        self.assertLess(
            metrics.processing_time,
            PERFORMANCE_THRESHOLDS[100000].max_processing_time_seconds,
            "100000x scale should process under the threshold",
        )
        self.assertLess(
            metrics.memory_usage_mb,
            PERFORMANCE_THRESHOLDS[100000].max_memory_usage_mb,
            "100000x scale should use less than the threshold",
        )

    def test_performance_scaling_cost_should_be_less_than_scaling_factor(self):
        """Test how performance scales across different data sizes."""
        scale_factors = [1, 10, 20, 50, 100]
        metrics_list = []

        for scale in scale_factors:
            metrics = self._measure_performance(scale)
            metrics_list.append((scale, metrics))
            print(f"\nScale {scale}x: {metrics.processing_time:.3f}s, {metrics.memory_usage_mb:.1f}MB")

        # Check that scaling cost is reasonable (not exponential)
        for i in range(1, len(metrics_list)):
            prev_scale, prev_metrics = metrics_list[i - 1]
            curr_scale, curr_metrics = metrics_list[i]

            scale_ratio = curr_scale / prev_scale
            time_ratio = curr_metrics.processing_time / prev_metrics.processing_time
            memory_ratio = (
                1 if prev_metrics.memory_usage_mb == 0 else curr_metrics.memory_usage_mb / prev_metrics.memory_usage_mb
            )

            # Time scaling should be roughly linear (not exponential)
            self.assertLess(
                time_ratio, scale_ratio * 2, f"Time scaling from {prev_scale}x to {curr_scale}x is too steep"
            )
            self.assertLess(
                memory_ratio, scale_ratio * 2, f"Memory scaling from {prev_scale}x to {curr_scale}x is too steep"
            )
