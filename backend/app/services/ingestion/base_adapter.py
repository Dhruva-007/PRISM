"""
Base adapter interface for PRISM data ingestion.

All external data source adapters must inherit from BaseAdapter
and implement the fetch() method.

This ensures:
- Consistent interface across all data sources
- Easy addition of new data sources in future phases
- Testability via mock adapters
"""

from abc import ABC, abstractmethod

import httpx

from app.models.community import CommunityEvent, DataSource
from app.utils.logging import get_logger


class BaseAdapter(ABC):
    """
    Abstract base class for all PRISM data source adapters.

    Each adapter is responsible for:
    1. Fetching raw data from its external source
    2. Normalizing it into CommunityEvent instances
    3. Handling source-specific errors gracefully

    Adapters must NEVER raise exceptions to their callers.
    All errors must be caught internally and logged.
    The fetch() method returns whatever events were successfully
    normalized, even if some records failed.
    """

    def __init__(self) -> None:
        self.logger = get_logger(self.__class__.__module__)
        self.source: DataSource = self._get_source()

    @abstractmethod
    def _get_source(self) -> DataSource:
        """Return the DataSource enum value for this adapter."""

    @abstractmethod
    async def fetch(
        self,
        latitude: float,
        longitude: float,
        city: str,
        city_id: str = "hyderabad",
    ) -> list[CommunityEvent]:
        """
        Fetch and normalize data from the external source.

        Args:
            latitude: Target location latitude
            longitude: Target location longitude
            city: Human-readable city name

        Returns:
            List of normalized CommunityEvent instances.
            Returns empty list if source is unavailable.
        """

    async def _get_http_client(self) -> httpx.AsyncClient:
        """
        Create a configured async HTTP client.

        Timeout: 15 seconds (external APIs can be slow)
        Follow redirects: True
        """
        return httpx.AsyncClient(
            timeout=httpx.Timeout(15.0),
            follow_redirects=True,
            headers={
                "User-Agent": "PRISM-DecisionIntelligence/1.0 (community-health-research)",
                "Accept": "application/json",
            },
        )