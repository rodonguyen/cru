from django.test import TestCase
from unittest.mock import patch, Mock, MagicMock
from pathlib import Path

from scheduler.services import get_schedule_data, _get_data_loader, _get_processor
from scheduler.loaders import DataLoader
from scheduler.processors import ScheduleDataProcessor, ScheduleProcessorError
import scheduler.services as services_module


class ScheduleServicesTestCase(TestCase):
    """Test cases for scheduler services layer."""

    def setUp(self):
        """Set up test fixtures."""
        # Reset global instances before each test
        services_module._data_loader = None
        services_module._processor = None

    def tearDown(self):
        """Clean up after each test."""
        # Reset global instances after each test
        services_module._data_loader = None
        services_module._processor = None

    def test_get_data_loader_creates_instance(self):
        """Test that _get_data_loader creates a new instance when none exists."""
        loader = _get_data_loader()

        self.assertIsInstance(loader, DataLoader)
        self.assertIsNotNone(services_module._data_loader)

    def test_get_data_loader_reuses_instance(self):
        """Test that _get_data_loader reuses existing instance."""
        loader1 = _get_data_loader()
        loader2 = _get_data_loader()

        self.assertIs(loader1, loader2)
        self.assertEqual(id(loader1), id(loader2))

    def test_get_processor_creates_instance(self):
        """Test that _get_processor creates a new instance when none exists."""
        processor = _get_processor()

        self.assertIsInstance(processor, ScheduleDataProcessor)
        self.assertIsNotNone(services_module._processor)

    def test_get_processor_reuses_instance(self):
        """Test that _get_processor reuses existing instance."""
        processor1 = _get_processor()
        processor2 = _get_processor()

        self.assertIs(processor1, processor2)
        self.assertEqual(id(processor1), id(processor2))

    def test_get_processor_uses_data_loader(self):
        """Test that _get_processor uses the data loader."""
        with patch("scheduler.services._get_data_loader") as mock_get_loader:
            mock_loader = Mock(spec=DataLoader)
            mock_get_loader.return_value = mock_loader

            processor = _get_processor()

            mock_get_loader.assert_called_once()
            self.assertIsInstance(processor, ScheduleDataProcessor)

    def test_services_integration(self):
        """Test full integration of services layer."""
        # This should work end-to-end with real data
        result = get_schedule_data()

        self.assertIsInstance(result, dict)
        self.assertIn("columns", result)
        self.assertIn("rows", result)
        self.assertIsInstance(result["columns"], list)
        self.assertIsInstance(result["rows"], list)
