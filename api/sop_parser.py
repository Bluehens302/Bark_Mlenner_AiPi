"""
SOP Parser Module
Extracts and parses numbered sections from PDF SOPs
"""
import os
import re
from typing import List, Dict, Optional
import pdfplumber
from pathlib import Path

class SOPParser:
    """Parse PDF SOPs and extract numbered sections"""

    def __init__(self, sops_directory: str):
        """
        Initialize SOP parser

        Args:
            sops_directory: Path to directory containing SOP PDFs
        """
        self.sops_dir = Path(sops_directory)
        self._sop_cache = {}

    def list_sops(self) -> List[Dict[str, str]]:
        """
        List all available SOP files

        Returns:
            List of dictionaries with sop_id and filename
        """
        sops = []

        if not self.sops_dir.exists():
            return sops

        for pdf_file in self.sops_dir.glob("*.pdf"):
            # Skip Zone.Identifier files
            if "Zone.Identifier" in pdf_file.name:
                continue

            sop_id = pdf_file.stem  # filename without extension
            sops.append({
                "sop_id": sop_id,
                "filename": pdf_file.name,
                "path": str(pdf_file)
            })

        return sops

    def extract_text_from_pdf(self, sop_id: str) -> Optional[str]:
        """
        Extract all text from a PDF

        Args:
            sop_id: SOP identifier (filename without extension)

        Returns:
            Full text content of PDF or None if not found
        """
        # Check cache first
        if sop_id in self._sop_cache:
            return self._sop_cache[sop_id]

        # Find the PDF file
        pdf_path = None
        for pdf_file in self.sops_dir.glob(f"{sop_id}*"):
            if pdf_file.suffix == ".pdf" and "Zone.Identifier" not in pdf_file.name:
                pdf_path = pdf_file
                break

        if not pdf_path or not pdf_path.exists():
            return None

        try:
            full_text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        full_text += text + "\n"

            # Cache the result
            self._sop_cache[sop_id] = full_text
            return full_text

        except Exception as e:
            print(f"Error extracting text from {pdf_path}: {e}")
            return None

    def parse_sections(self, sop_id: str) -> List[Dict[str, str]]:
        """
        Parse numbered sections from SOP

        Looks for patterns like:
        - "1. Section Title"
        - "2.1 Subsection"
        - "Section 1: Title"

        Args:
            sop_id: SOP identifier

        Returns:
            List of sections with section_number, title, and content
        """
        text = self.extract_text_from_pdf(sop_id)
        if not text:
            return []

        sections = []

        # Pattern to match numbered sections
        # Matches: "1.", "1.1", "2.3.4", "Section 1:", etc.
        section_pattern = re.compile(
            r'^(?:Section\s+)?(\d+(?:\.\d+)*)[\.:\s]\s*(.+?)$',
            re.MULTILINE | re.IGNORECASE
        )

        matches = list(section_pattern.finditer(text))

        # Filter to only major sections (ALL CAPS or mostly uppercase titles)
        major_sections = []
        for match in matches:
            section_number = match.group(1)
            title = match.group(2).strip()

            # Only include if:
            # 1. Title is mostly uppercase (ALL CAPS section headings)
            # 2. OR title length > 15 chars and > 70% uppercase
            # 3. OR section number is single digit (top-level sections like "1.", "2.")

            uppercase_ratio = sum(1 for c in title if c.isupper()) / max(len(title.replace(' ', '')), 1)
            is_all_caps = uppercase_ratio > 0.7 and len(title) > 5
            is_top_level = '.' not in section_number  # Single digit like "1", "2", not "1.1"

            if is_all_caps or (is_top_level and len(title) > 10):
                major_sections.append((match, section_number, title))

        for i, (match, section_number, title) in enumerate(major_sections):
            # Get content between this section and the next major section
            start_pos = match.end()
            if i + 1 < len(major_sections):
                end_pos = major_sections[i + 1][0].start()
            else:
                end_pos = len(text)

            content = text[start_pos:end_pos].strip()

            # Clean up content
            content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)  # Remove excessive newlines

            sections.append({
                "section_number": section_number,
                "title": title,
                "content": content,
                "full_heading": f"{section_number}. {title}"
            })

        return sections

    def get_section(self, sop_id: str, section_number: str) -> Optional[Dict[str, str]]:
        """
        Get a specific section by number

        Args:
            sop_id: SOP identifier
            section_number: Section number (e.g., "1", "2.1", "3.2.1")

        Returns:
            Section dictionary or None if not found
        """
        sections = self.parse_sections(sop_id)

        for section in sections:
            if section["section_number"] == section_number:
                return section

        return None

    def search_sections(self, query: str) -> List[Dict[str, str]]:
        """
        Search for sections across all SOPs that match a query

        Args:
            query: Search term (searches in titles and content)

        Returns:
            List of matching sections with sop_id included
        """
        results = []
        query_lower = query.lower()

        for sop_info in self.list_sops():
            sop_id = sop_info["sop_id"]
            sections = self.parse_sections(sop_id)

            for section in sections:
                # Search in title and content
                if (query_lower in section["title"].lower() or
                    query_lower in section["content"].lower()):

                    result = section.copy()
                    result["sop_id"] = sop_id
                    result["sop_filename"] = sop_info["filename"]
                    results.append(result)

        return results

    def map_section_to_calculator(self, section_title: str, section_content: str) -> List[str]:
        """
        Determine which calculator(s) are relevant for a section

        Args:
            section_title: Section title
            section_content: Section content

        Returns:
            List of calculator names that are relevant
        """
        calculators = []

        # Combine title and content for searching
        text = (section_title + " " + section_content).lower()

        # Map keywords to calculators
        calculator_keywords = {
            "pcr": ["pcr", "primer", "annealing", "thermocycler", "amplification"],
            "gibson": ["gibson", "assembly", "gibson assembly", "fragment"],
            "restriction": ["restriction", "digest", "restriction enzyme", "cut"],
            "ligation": ["ligation", "ligate", "insert", "vector", "clone"],
            "oligo": ["oligo", "annealing", "oligonucleotide"]
        }

        for calc_name, keywords in calculator_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    if calc_name not in calculators:
                        calculators.append(calc_name)
                    break

        return calculators

    def get_section_with_calculator(self, sop_id: str, section_number: str) -> Optional[Dict]:
        """
        Get section with suggested calculator

        Args:
            sop_id: SOP identifier
            section_number: Section number

        Returns:
            Section with suggested_calculators field
        """
        section = self.get_section(sop_id, section_number)

        if section:
            calculators = self.map_section_to_calculator(
                section["title"],
                section["content"]
            )
            section["suggested_calculators"] = calculators
            section["sop_id"] = sop_id

        return section
