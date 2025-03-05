from typing import Dict
import logging
from ..services.dailymed_service import DailyMedService
from ..extractor.dailymed_extractor import DailyMedExtractor

logger = logging.getLogger(__name__)


class DailyMedProcessor:
    def __init__(self):
        self.service = DailyMedService()
        self.extractor = DailyMedExtractor()

    async def get_drug_indications(self, drug_name: str) -> Dict:
        """Process and get indications for a drug.

        Args:
            drug_name (str): Name of the drug to get indications for

        Returns:
            Dict: Dictionary containing drug information, indications, directions, and any errors
        """
        try:
            async with self.service as service:
                # Get SPL info for the drug
                spl_info = await service.get_spl_info(drug_name)
                if not spl_info:
                    return {
                        "drug": drug_name,
                        "set_id": None,
                        "indication": None,
                        "directions": None,
                        "error": "No SPL information found",
                    }

                # Get detailed SPL XML
                set_id = spl_info.get("setid")
                if not set_id:
                    return {
                        "drug": drug_name,
                        "set_id": None,
                        "indication": None,
                        "directions": None,
                        "error": "No SetID found",
                    }

                xml_content = await service.get_spl_details(set_id)
                if not xml_content:
                    return {
                        "drug": drug_name,
                        "set_id": set_id,
                        "indication": None,
                        "directions": None,
                        "error": "No XML content found",
                    }

                # Extract indications and directions using the extractor
                indication = self.extractor.extract_indication(xml_content)
                directions = self.extractor.extract_directions(xml_content)

                return {
                    "drug": drug_name,
                    "set_id": set_id,
                    "indication": indication,
                    "directions": directions,
                    "error": None,
                }
        except Exception as e:
            logger.error(f"Error processing drug indications for {drug_name}: {str(e)}")
            return {
                "drug": drug_name,
                "set_id": None,
                "indication": None,
                "directions": None,
                "error": f"Processing error: {str(e)}",
            }
