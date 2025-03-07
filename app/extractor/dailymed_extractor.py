from bs4 import BeautifulSoup
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

# Keywords to look for in section titles
INDICATION_KEYWORDS = [
    "Indications",
    "Indication",
    "Use",
    "Uses",
    "Usage",
    "INDICATIONS AND USAGE",
    "INDICATIONS & USAGE",
    "INDICATIONS &amp; USAGE",
]

DIRECTION_KEYWORDS = [
    "Directions",
    "Direction",
    "Administration",
    "DOSAGE AND ADMINISTRATION",
    "DOSAGE & ADMINISTRATION",
    "How to use",
    "Method of Administration",
]


class DailyMedExtractor:
    @staticmethod
    def get_text_content(element) -> str:
        """Helper function to get all text content, including styled text"""
        if not element:
            return ""
        # Get all text, including text within content tags
        text = ""
        for child in element.children:
            if child.name == "content":
                text += child.get_text(strip=True)
            elif child.string:
                text += child.string.strip()
        return text.strip()

    @staticmethod
    def process_table(table) -> List[str]:
        """Helper function to process table content"""
        table_content = []
        for row in table.find_all("tr"):
            row_text = []
            for cell in row.find_all(["td", "th"]):
                cell_text = DailyMedExtractor.get_text_content(cell)
                if cell_text:
                    row_text.append(cell_text)
            if row_text:
                table_content.append(" - ".join(row_text))
        return table_content

    def extract_indication(self, xml_content: str) -> str:
        """Extract indications from SPL XML content."""
        try:
            soup = BeautifulSoup(xml_content, "xml")
            indications = []

            # Find all sections
            sections = soup.find_all("section")

            for section in sections:
                # Check for LOINC code 34067-9 (INDICATIONS & USAGE SECTION)
                if section.find("code", {"code": "34067-9"}):
                    text_content = section.find("text")
                    if text_content:
                        # Handle paragraphs
                        for paragraph in text_content.find_all("paragraph"):
                            text = self.get_text_content(paragraph)
                            if text:
                                indications.append(text)

                        # Handle lists
                        for list_elem in text_content.find_all("list"):
                            for item in list_elem.find_all("item"):
                                text = self.get_text_content(item)
                                if text:
                                    indications.append(text)

                        # Handle direct text content
                        text = self.get_text_content(text_content)
                        if text and text not in indications:
                            indications.append(text)
                    continue

                # Check section title for indication keywords
                title = section.find("title")
                if title:
                    title_text = self.get_text_content(title).lower()
                    if any(
                        keyword.lower() == title_text for keyword in INDICATION_KEYWORDS
                    ):
                        text_content = section.find("text")
                        if text_content:
                            # Handle paragraphs
                            for paragraph in text_content.find_all("paragraph"):
                                text = self.get_text_content(paragraph)
                                if text:
                                    indications.append(text)

                            # Handle lists
                            for list_elem in text_content.find_all("list"):
                                for item in list_elem.find_all("item"):
                                    text = self.get_text_content(item)
                                    if text:
                                        indications.append(text)

                            # Handle direct text content
                            text = self.get_text_content(text_content)
                            if text and text not in indications:
                                indications.append(text)

            # Remove duplicates while preserving order
            seen = set()
            return [x for x in indications if not (x in seen or seen.add(x))]
        except Exception as e:
            logger.error(f"Error extracting indications: {str(e)}")
            return None

    def extract_directions(self, xml_content: str) -> str:
        """Extract directions/dosage information from SPL XML content."""
        try:
            soup = BeautifulSoup(xml_content, "xml")
            directions = []

            # Find all sections
            sections = soup.find_all("section")

            for section in sections:
                # Check for LOINC code 34068-7 (DOSAGE & ADMINISTRATION SECTION)
                if section.find("code", {"code": "34068-7"}):
                    text_content = section.find("text")
                    if text_content:
                        # Handle paragraphs
                        for paragraph in text_content.find_all("paragraph"):
                            text = self.get_text_content(paragraph)
                            if text:
                                directions.append(text)

                        # Handle lists
                        for list_elem in text_content.find_all("list"):
                            for item in list_elem.find_all("item"):
                                text = self.get_text_content(item)
                                if text:
                                    directions.append("• " + text)

                        # Handle tables
                        for table in text_content.find_all("table"):
                            table_content = self.process_table(table)
                            directions.extend(table_content)

                        # Handle direct text content
                        text = self.get_text_content(text_content)
                        if text and text not in directions:
                            directions.append(text)
                    continue

                # Check section title for direction keywords
                title = section.find("title")
                if title:
                    title_text = self.get_text_content(title).lower()
                    if any(
                        keyword.lower() in title_text for keyword in DIRECTION_KEYWORDS
                    ):
                        text_content = section.find("text")
                        if text_content:
                            # Handle paragraphs
                            for paragraph in text_content.find_all("paragraph"):
                                text = self.get_text_content(paragraph)
                                if text:
                                    directions.append(text)

                            # Handle lists
                            for list_elem in text_content.find_all("list"):
                                for item in list_elem.find_all("item"):
                                    text = self.get_text_content(item)
                                    if text:
                                        directions.append("• " + text)

                            # Handle tables
                            for table in text_content.find_all("table"):
                                table_content = self.process_table(table)
                                directions.extend(table_content)

                            # Handle direct text content
                            text = self.get_text_content(text_content)
                            if text and text not in directions:
                                directions.append(text)

            # Remove duplicates while preserving order
            seen = set()
            unique_directions = [
                x for x in directions if not (x in seen or seen.add(x))
            ]

            # Join with newlines to preserve formatting
            return "\n".join(unique_directions)

        except Exception as e:
            logger.error(f"Error extracting directions: {str(e)}")
            return None
