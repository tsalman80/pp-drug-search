import aiohttp
from typing import List, Dict, Optional
import logging
from ..core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class DailyMedService:
    def __init__(self):
        self.base_url = settings.DAILYMED_BASE_URL
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def get_drug_names(self, page: int = 1) -> Dict:
        """Fetch drug names from DailyMed API."""
        try:
            async with self.session.get(
                f"{settings.DAILYMED_DRUGNAMES_ENDPOINT}",
                params={"page": page, "pagesize": 100},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data
        except Exception as e:
            logger.error(f"Error fetching drug names: {str(e)}")
            return None

    async def get_spl_info(self, drug_name: str) -> Optional[Dict]:
        """Fetch SPL information for a drug."""
        try:
            async with self.session.get(
                f"{settings.DAILYMED_SPLS_ENDPOINT}", params={"drug_name": drug_name}
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("data", [{}])[0] if data.get("data") else None
        except Exception as e:
            logger.error(f"Error fetching SPL info for {drug_name}: {str(e)}")
            return None

    async def get_spl_all(self, drug_name: str) -> Optional[List[Dict]]:
        """Fetch SPL information for a drug."""
        try:
            async with self.session.get(
                f"{settings.DAILYMED_SPLS_ENDPOINT}",
                params={"drug_name": drug_name, "pagesize": 100},
            ) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("data", []) if data.get("data") else []
        except Exception as e:
            logger.error(f"Error fetching SPL info for {drug_name}: {str(e)}")
            return []

    async def get_spl_details(self, set_id: str) -> Optional[str]:
        """Fetch detailed SPL XML for a drug."""
        try:
            async with self.session.get(
                f"{settings.DAILYMED_SPL_DETAIL_ENDPOINT}/{set_id}.xml"
            ) as response:
                response.raise_for_status()
                return await response.text()
        except Exception as e:
            logger.error(f"Error fetching SPL details for {set_id}: {str(e)}")
            return None
