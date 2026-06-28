import logging
from typing import List, Dict
from app.experience_bank import ExperienceBank
from app.database import Database
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class CoverLetterGenerator:
    """Generate tailored cover letters based on JD and resume."""

    def __init__(self, db: Database, api_key: str):
        self.db = db
        self.client = Anthropic(api_key=api_key)
        self.bank = ExperienceBank(db)

    def generate(
        self,
        jd_text: str,
        jd_keywords: List[str],
        company: str,
        role: str,
        your_name: str = "Mohammed"
    ) -> str:
        """Generate a tailored cover letter."""
        logger.info(f"Generating cover letter for {company} - {role}")

        # Get all experience bank entries
        all_entries = self.bank.get_all_entries()
        resume_content = self._format_resume_content(all_entries)

        prompt = f"""Generate a professional cover letter (3-4 paragraphs) for a job application.
Use ONLY the resume content provided. Never fabricate experience.

**Applicant Name:** {your_name}

**Company:** {company}
**Role:** {role}

**Key JD Keywords:** {', '.join(jd_keywords[:8])}

**JD Excerpt:**
{jd_text[:1000]}

**Resume Content (use ONLY what's provided):**
{resume_content}

**Cover Letter Structure:**
1. Paragraph 1: Introduction + why interested in the company/role (2-3 sentences)
2. Paragraph 2: Key relevant experience + skills that match JD (3-4 sentences)
3. Paragraph 3: Soft skills / team fit / cultural alignment (2-3 sentences)
4. Paragraph 4: Closing + next steps (1-2 sentences)

**Requirements:**
- Professional, first-person, conversational tone
- Ground ALL content in the provided resume
- Never invent experience, projects, or skills
- Address the specific company and role
- 3-4 paragraphs, ~400 words total
- If information is limited in resume, focus on what's available

Respond with ONLY the cover letter text, starting with "Dear Hiring Manager," or appropriate greeting."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=600,
                messages=[{"role": "user", "content": prompt}]
            )

            cover_letter = message.content[0].text.strip()
            logger.info(f"Generated cover letter for {company} - {role}")
            return cover_letter

        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            raise

    def _format_resume_content(self, entries: List[Dict]) -> str:
        """Format experience bank entries as resume text."""
        content = "Resume Content:\n\n"

        # Get summary if available
        summary_entries = [e for e in entries if e.get("category") == "summary"]
        if summary_entries:
            content += "**Professional Summary:**\n"
            content += summary_entries[0]["content"] + "\n\n"

        # Get experience
        bullet_entries = [e for e in entries if e.get("category") == "bullet"]
        if bullet_entries:
            content += "**Work Experience Highlights:**\n"
            for entry in bullet_entries[:8]:
                content += f"- {entry['content']}\n"
            content += "\n"

        # Get skills
        skill_entries = [e for e in entries if e.get("category") == "skill"]
        if skill_entries:
            content += "**Skills:**\n"
            skills = [e["content"] for e in skill_entries[:15]]
            content += ", ".join(skills) + "\n\n"

        # Get projects
        project_entries = [e for e in entries if e.get("category") == "project"]
        if project_entries:
            content += "**Projects:**\n"
            for entry in project_entries[:3]:
                content += f"- {entry['content']}\n"
            content += "\n"

        return content
