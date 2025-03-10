import os
import pymupdf  # PyMuPDF
import aiohttp
import asyncio
from typing import Optional
from pathlib import Path
from bs4 import BeautifulSoup
import pymupdf4llm


class PDFService:
    def __init__(self, download_dir: str = "data/pdfs"):
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)

    async def download_pdf(self, setid: str) -> Optional[str]:
        """Download PDF file from DailyMed."""
        url = f"https://dailymed.nlm.nih.gov/dailymed/downloadpdffile.cfm?setId={setid}"
        file_path = self.download_dir / f"{setid}.pdf"

        if file_path.exists():
            return str(file_path)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                    return str(file_path)
                return None

    async def download_markdown(self, setid: str) -> Optional[str]:
        """Download PDF file from DailyMed."""
        url = f"https://dailymed.nlm.nih.gov/dailymed/fda/fdaDrugXsl.cfm?setid={setid}"
        file_path = self.download_dir / f"{setid}.html"

        if file_path.exists():
            return str(file_path)

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    with open(file_path, "wb") as f:
                        f.write(content)
                    return str(file_path)
                return None

    def extract_indications_section(self, file_path: str) -> Optional[list[str]]:
        """Extract the INDICATIONS AND USAGE section from the HTML and return as list of indications.

        Args:
            file_path: Path to the HTML file

        Returns:
            Optional[list[str]]: List of individual indications, or None if section not found
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            soup = BeautifulSoup(html_content, "html.parser")

            # Find the section with data-sectioncode="34067-9"
            indications_section = soup.find("div", {"data-sectioncode": "34067-9"})
            if not indications_section:
                return None

            # Find all div elements in the section
            content_sections = indications_section.find_all("div", recursive=True)

            if len(content_sections) == 0:
                content_sections = indications_section

            # Initialize list to store text from each div
            extracted_indications = []

            # Process each div's text content
            for section in content_sections:
                # Get all text content within this div, preserving structure
                section_text = ". ".join(
                    s.strip() for s in section.strings if s.strip()
                )
                if section_text:
                    extracted_indications.append(section_text)

            # Clean up and remove duplicates while preserving order
            seen = set()
            indications = []
            for text in extracted_indications:
                if text not in seen and not "indications and usage" in text.lower():
                    seen.add(text)
                    indications.append(text)

            # If no content found, return None
            if not indications:
                return None

            return indications

        except Exception as e:
            print(f"Error processing HTML {file_path}: {str(e)}")
            return None

    async def process_drug_pdf(self, setid: str) -> Optional[list[str]]:
        """Download PDF and extract indications section."""
        file_path = await self.download_markdown(setid)
        if file_path:
            return self.extract_indications_section(file_path)
        return None


# Create a singleton instance
pdf_service = PDFService()
