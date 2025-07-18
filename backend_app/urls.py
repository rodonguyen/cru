from django.urls import path, include

# API URL patterns
urlpatterns = [
    path("api/", include("scheduler.urls")),
]
