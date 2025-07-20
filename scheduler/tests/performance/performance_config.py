"""
Performance testing configuration and utilities.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class PerformanceThresholds:
    """Performance test thresholds for different scale factors."""

    max_processing_time_seconds: float
    max_memory_usage_mb: float
    max_peak_memory_mb: float
    description: str


# Performance thresholds by scale factor
PERFORMANCE_THRESHOLDS = {
    1: PerformanceThresholds(
        max_processing_time_seconds=0.05,
        max_memory_usage_mb=0.3,
        max_peak_memory_mb=75,
        description="Baseline - current dataset size",
    ),
    1000: PerformanceThresholds(
        max_processing_time_seconds=0.5,
        max_memory_usage_mb=50,
        max_peak_memory_mb=150,
        description="1000x scale - small enterprise",
    ),
    10000: PerformanceThresholds(
        max_processing_time_seconds=4,
        max_memory_usage_mb=450,
        max_peak_memory_mb=800,
        description="10000x scale - medium enterprise",
    ),
    100000: PerformanceThresholds(
        max_processing_time_seconds=40,
        max_memory_usage_mb=4500,
        max_peak_memory_mb=7500,
        description="100 000x scale - large enterprise",
    ),
}

# Testing scenarios for different use cases
TESTING_SCENARIOS = {
    "baseline": {"scale_factor": 1, "description": "Initial development load"},
    "1000x": {
        "scale_factor": 1000,
        "description": "Stress test x1000 - large enterprise",
    },
    "10000x": {
        "scale_factor": 10000,
        "description": "Stress test x10000 - large enterprise",
    },
    "100 000 x": {
        "scale_factor": 100000,
        "description": "Stress test x100 000 - very large enterprise",
    },
}
