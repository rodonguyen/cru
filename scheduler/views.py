import logging
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

from .services import get_schedule_data
from .loaders import DataLoaderError
from .processors import ScheduleProcessorError

logger = logging.getLogger(__name__)


@api_view(["GET"])
def schedule_table(request) -> Response:
    """
    Return formatted schedule data for frontend table consumption.
    """
    try:
        logger.info("Processing schedule table request")

        data = get_schedule_data()

        logger.info(f"Successfully returned schedule data with {len(data.get('rows', []))} rows")
        return Response(data, status=status.HTTP_200_OK)

    except DataLoaderError as e:
        logger.error(f"Data loading error: {e}")
        return Response(
            {
                "error": "Failed to load data from JSON files",
                "detail": str(e),
                "code": "DATA_LOAD_ERROR",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except ScheduleProcessorError as e:
        logger.error(f"Data processing error: {e}")
        return Response(
            {
                "error": "Failed to process schedule data",
                "detail": str(e),
                "code": "PROCESSING_ERROR",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    except Exception as e:
        logger.exception(f"Unexpected error in schedule_table: {e}")
        return Response(
            {
                "error": "Internal server error",
                "detail": "An unexpected error occurred",
                "code": "INTERNAL_ERROR",
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
