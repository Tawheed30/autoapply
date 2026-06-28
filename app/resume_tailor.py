import logging
import json
from pathlib import Path
from typing import Dict, List, Tuple, Optional, TYPE_CHECKING
from docx import Document
from docx.oxml.ns import qn
from anthropic import Anthropic

if TYPE_CHECKING:
    from docx.document import Document as DocxDocument

logger = logging.getLogger(__name__)


class ResumeTailor:
    """Tailor resume while preserving layout using Claude."""

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.changes = []  # Track all changes for diff

    def tailor_resume(
        self,
        master_docx_path: str,
        jd_text: str,
        jd_keywords: List[str],
        match_report: Dict,
        output_path: str,
    ):
        """
        Tailor a resume for a specific JD while preserving layout.

        Returns:
            (output_file_path, list_of_changes)
        """
        self.changes = []

        # Load the master resume
        doc = Document(master_docx_path)
        logger.info(f"Loaded master resume from {master_docx_path}")

        # Identify editable sections
        editable_sections = self._identify_editable_sections(doc)
        logger.info(f"Found {len(editable_sections)} editable sections")

        # Tailor each section
        for section_info in editable_sections:
            original_text = section_info["original_text"]
            para = section_info["paragraph"]
            run = section_info["run"]

            # Decide if this should be tailored
            if self._should_tailor(section_info):
                new_text = self._rewrite_text(
                    original_text,
                    jd_text,
                    jd_keywords,
                    match_report,
                    section_info["section_type"],
                )

                if new_text and new_text != original_text:
                    # Update the run while preserving formatting
                    self._update_run(run, new_text)

                    # Log the change
                    self.changes.append({
                        "original": original_text,
                        "new": new_text,
                        "section_type": section_info["section_type"],
                    })
                    logger.info(f"Updated: {original_text[:50]}... → {new_text[:50]}...")

        # Verify layout is preserved
        logger.info(f"Made {len(self.changes)} changes to resume")

        # Save tailored resume
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_path)
        logger.info(f"Saved tailored resume to {output_path}")

        return output_path, self.changes

    def _identify_editable_sections(self, doc) -> List[Dict]:
        """Identify paragraphs/runs that are editable (not headings, dates, company names)."""
        editable = []

        for para_idx, para in enumerate(doc.paragraphs):
            # Skip empty paragraphs
            if not para.text.strip():
                continue

            # Skip if it looks like a heading (all caps, short, large font)
            if self._is_heading(para):
                continue

            # Skip if it's a date range
            if self._is_date_range(para.text):
                continue

            # Iterate through runs in the paragraph
            for run in para.runs:
                text = run.text.strip()
                if not text:
                    continue

                # Skip company names (all caps, or marked as bold)
                if self._is_company_name(text, run):
                    continue

                # Skip dates
                if self._is_date_range(text):
                    continue

                # Classify the section type
                section_type = self._classify_section(para)

                editable.append({
                    "paragraph": para,
                    "run": run,
                    "original_text": text,
                    "section_type": section_type,
                    "para_idx": para_idx,
                })

        return editable

    def _should_tailor(self, section_info: Dict) -> bool:
        """Decide if a section should be tailored."""
        # Tailor bullets, skills, and summary
        return section_info["section_type"] in ["bullet", "skill", "summary"]

    def _classify_section(self, para) -> str:
        """Classify a paragraph as bullet, company, title, date, summary, skill, or other."""
        text = para.text.strip()
        text_lower = text.lower()

        # Bullet points
        if text.startswith(("•", "-", "*", "◦")):
            return "bullet"

        # Keywords suggest section type
        if any(kw in text_lower for kw in ["skill", "technical", "competencies", "expertise"]):
            return "skill"

        if any(kw in text_lower for kw in ["summary", "profile", "objective"]):
            return "summary"

        # Check if it's a skill (comma-separated or single skill)
        if "," in text and len(text) < 100:
            return "skill"

        return "other"

    def _is_heading(self, para) -> bool:
        """Check if paragraph is a heading."""
        text = para.text.strip()

        # Check style
        if para.style and "heading" in para.style.name.lower():
            return True

        # All caps + short
        if text.isupper() and len(text) < 50:
            return True

        # Check formatting (bold, large font)
        for run in para.runs:
            if run.font.size and run.font.size.pt > 12:
                return True
            if run.font.bold:
                return True

        return False

    def _is_date_range(self, text: str) -> bool:
        """Check if text is a date range."""
        import re
        date_pattern = r'\d{1,2}/\d{1,2}/\d{4}|[A-Z][a-z]{2} \d{4}|20\d{2}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|to|–|-'
        return bool(re.search(date_pattern, text))

    def _is_company_name(self, text: str, run) -> bool:
        """Check if text is likely a company name."""
        # All caps and not too long
        if text.isupper() and 5 < len(text) < 50:
            return True

        # Check if bold (safely)
        try:
            if run.font.bold:
                return True
        except:
            pass

        return False

    def _update_run(self, run, new_text: str):
        """Update the text in a run while preserving formatting."""
        run.text = new_text

    def _rewrite_text(
        self,
        original: str,
        jd_text: str,
        jd_keywords: List[str],
        match_report: Dict,
        section_type: str,
    ) -> Optional[str]:
        """Call Claude to rewrite text for JD relevance."""
        prompt = self._build_rewrite_prompt(
            original,
            jd_text,
            jd_keywords,
            match_report,
            section_type,
        )

        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
            )

            response_text = message.content[0].text.strip()

            # Extract the rewritten text (may be wrapped in quotes or markers)
            if response_text.startswith('"') and response_text.endswith('"'):
                response_text = response_text[1:-1]
            elif response_text.startswith("'") and response_text.endswith("'"):
                response_text = response_text[1:-1]

            logger.info(f"Rewrote: {original[:40]}... → {response_text[:40]}...")
            return response_text

        except Exception as e:
            logger.error(f"Error rewriting text: {e}")
            return original

    def _build_rewrite_prompt(
        self,
        original: str,
        jd_text: str,
        jd_keywords: List[str],
        match_report: Dict,
        section_type: str,
    ) -> str:
        """Build a prompt for Claude to rewrite a resume section."""
        keywords_str = ", ".join(jd_keywords[:10])
        matched = ", ".join(match_report.get("matched_keywords", [])[:5])
        missing = ", ".join(match_report.get("missing_keywords", [])[:5])

        prompt = f"""You are a resume expert. Rewrite this resume text to emphasize relevance to a job description while keeping it truthful and using only the same experience.

**Original text:**
{original}

**Job posting keywords (top 10):**
{keywords_str}

**My skills already matching the JD:**
{matched}

**Skills the JD wants that I might emphasize:**
{missing}

**Task:**
- Reword the text to highlight the most relevant keywords from the JD
- Use the exact same experience/facts; never fabricate or exaggerate
- Keep the same length and style
- Do NOT add skills or experience I don't have
- Only emphasize what's already there

Respond with ONLY the rewritten text, no explanation."""

        return prompt

    def generate_diff(self) -> List[Dict]:
        """Generate a before/after diff of all changes."""
        return [
            {
                "type": "change",
                "section": change["section_type"],
                "before": change["original"],
                "after": change["new"],
            }
            for change in self.changes
        ]

    def save_diff_report(self, output_path: str):
        """Save a detailed diff report to a file."""
        diff = self.generate_diff()

        report = "# Resume Tailoring Diff Report\n\n"
        for i, change in enumerate(diff, 1):
            report += f"## Change {i} ({change['section'].upper()})\n\n"
            report += f"**Before:**\n```\n{change['before']}\n```\n\n"
            report += f"**After:**\n```\n{change['after']}\n```\n\n"

        Path(output_path).write_text(report)
        logger.info(f"Saved diff report to {output_path}")
