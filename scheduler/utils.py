from typing import Dict, Optional
import logging

from .loaders import DataLoader, DataLoaderError
from .processors import ScheduleDataProcessor, ScheduleProcessorError

logger = logging.getLogger(__name__)

# Global instances for efficient caching
_data_loader: Optional[DataLoader] = None
_processor: Optional[ScheduleDataProcessor] = None


def _get_data_loader() -> DataLoader:
    """Get or create the global DataLoader instance."""
    global _data_loader
    if _data_loader is None:
        _data_loader = DataLoader()
        logger.debug("Created new DataLoader instance")
    return _data_loader


def _get_processor() -> ScheduleDataProcessor:
    """Get or create the global ScheduleDataProcessor instance."""
    global _processor
    if _processor is None:
        _processor = ScheduleDataProcessor(_get_data_loader())
        logger.debug("Created new ScheduleDataProcessor instance")
    return _processor


def get_schedule_data() -> Dict:
    """
    Public interface to get processed schedule data.

    Returns:
        Dictionary with 'columns' and 'rows' keys for frontend consumption

    Raises:
        DataLoaderError: If data cannot be loaded from JSON files
        ScheduleProcessorError: If data processing fails
    """
    try:
        processor = _get_processor()
        return processor.process_schedule_data()
    except (DataLoaderError, ScheduleProcessorError) as e:
        logger.error(f"Failed to get schedule data: {e}")
        raise
