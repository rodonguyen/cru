"""
Django 5.2 URL configuration for scheduler app.

Following Django 5.2 best practices for URL patterns and organization.
"""

from django.urls import path
from . import views

app_name = "scheduler"

urlpatterns = [
    # Main schedule data endpoint for frontend consumption
    path("schedule-table/", views.schedule_table, name="schedule_table")
]
