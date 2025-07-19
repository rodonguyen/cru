from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch

from scheduler.loaders import DataLoaderError
from scheduler.processors import ScheduleProcessorError


class ScheduleAPITestCase(TestCase):
    """Test cases for Schedule API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        self.schedule_url = reverse("scheduler:schedule_table")

    def test_schedule_table_success(self):
        """Test successful schedule table response."""
        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("columns", response.data)
        self.assertIn("rows", response.data)
        self.assertIsInstance(response.data["columns"], list)
        self.assertIsInstance(response.data["rows"], list)

    def test_schedule_table_headers(self):
        """Test API response headers and content type."""
        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "application/json")

    @patch("scheduler.views.get_schedule_data")
    def test_schedule_table_data_loader_error(self, mock_get_data):
        """Test API response when DataLoaderError occurs."""
        mock_get_data.side_effect = DataLoaderError("Test data loading error")

        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["code"], "DATA_LOAD_ERROR")
        self.assertIn("Failed to load data from JSON files", response.data["error"])

    @patch("scheduler.views.get_schedule_data")
    def test_schedule_table_processor_error(self, mock_get_data):
        """Test API response when ScheduleProcessorError occurs."""
        mock_get_data.side_effect = ScheduleProcessorError("Test processing error")

        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["code"], "PROCESSING_ERROR")
        self.assertIn("Failed to process schedule data", response.data["error"])

    @patch("scheduler.views.get_schedule_data")
    def test_schedule_table_unexpected_error(self, mock_get_data):
        """Test API response when unexpected error occurs."""
        mock_get_data.side_effect = ValueError("Unexpected error")

        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertIn("error", response.data)
        self.assertEqual(response.data["code"], "INTERNAL_ERROR")
        self.assertIn("An unexpected error occurred", response.data["error"])

    def test_schedule_table_response_structure(self):
        """Test that response has expected structure and data types."""
        response = self.client.get(self.schedule_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify response structure
        self.assertIn("columns", response.data)
        self.assertIn("rows", response.data)

        # Verify data types
        self.assertIsInstance(response.data["columns"], list)
        self.assertIsInstance(response.data["rows"], list)

        # If there's data, verify column structure
        if response.data["columns"]:
            self.assertEqual(response.data["columns"][0], "Name")

        # If there are rows, verify row structure
        if response.data["rows"]:
            first_row = response.data["rows"][0]
            self.assertIsInstance(first_row, list)
            self.assertTrue(len(first_row) >= 1)  # At least name column
