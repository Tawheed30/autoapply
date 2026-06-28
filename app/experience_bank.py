import logging
from typing import List, Dict
from app.database import Database
from app.resume_parser import ResumeParser

logger = logging.getLogger(__name__)


class ExperienceBank:
    def __init__(self, db: Database):
        self.db = db

    def populate_from_resume(self, docx_path: str) -> int:
        """Parse a resume and populate the experience bank with all content."""
        parser = ResumeParser(docx_path)
        sections = parser.parse_resume()

        count = 0

        # Add summary
        if sections.get("summary"):
            self.add_entry("summary", sections["summary"], themes="general")
            count += 1

        # Add skills
        for skill in sections.get("skills", []):
            if skill:
                self.add_entry("skill", skill, themes="technical")
                count += 1

        # Add experience bullets with themes
        for exp in sections.get("experience", []):
            company = exp.get("company", "Unknown")
            title = exp.get("title", "Unknown")
            role_source = f"{company} - {title}"

            for bullet in exp.get("bullets", []):
                if bullet:
                    # Detect themes from content
                    themes = self._detect_themes(bullet)
                    self.add_entry("bullet", bullet, themes=themes, role_source=role_source)
                    count += 1

        # Add education
        for edu in sections.get("education", []):
            if edu:
                self.add_entry("education", edu, themes="education")
                count += 1

        # Add certifications
        for cert in sections.get("certifications", []):
            if cert:
                self.add_entry("certification", cert, themes="certification")
                count += 1

        # Add projects
        for project in sections.get("projects", []):
            if project:
                self.add_entry("project", project, themes="project")
                count += 1

        logger.info(f"Populated experience bank with {count} entries")
        self.db.log_activity("populate_experience_bank", "experience_bank", f"Added {count} entries")
        return count

    def add_entry(self, category: str, content: str, themes: str = None, role_source: str = None) -> int:
        """Add a single entry to the experience bank."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO experience_bank (category, content, themes, role_source)
            VALUES (?, ?, ?, ?)
        """, (category, content, themes or "", role_source or ""))

        entry_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return entry_id

    def get_entries_by_category(self, category: str) -> List[Dict]:
        """Retrieve all entries of a specific category."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, category, content, themes, role_source FROM experience_bank
            WHERE category = ?
            ORDER BY id
        """, (category,))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_all_entries(self) -> List[Dict]:
        """Retrieve all entries from the experience bank."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, category, content, themes, role_source FROM experience_bank
            ORDER BY category, id
        """)

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def search_by_themes(self, theme: str) -> List[Dict]:
        """Search entries by theme."""
        conn = self.db.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, category, content, themes FROM experience_bank
            WHERE themes LIKE ?
            ORDER BY id
        """, (f"%{theme}%",))

        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def clear_bank(self):
        """Clear all entries from the experience bank (for testing)."""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM experience_bank")
        conn.commit()
        conn.close()
        logger.info("Experience bank cleared")

    def _detect_themes(self, text: str) -> str:
        """Detect and tag themes from content."""
        themes = []
        text_lower = text.lower()

        theme_keywords = {
            "security": ["security", "vulnerability", "exploit", "threat", "incident", "breach", "attack"],
            "cloud": ["aws", "azure", "gcp", "cloud", "ec2", "s3", "lambda"],
            "automation": ["automation", "script", "orchestration", "ansible", "terraform", "ci/cd"],
            "analysis": ["analysis", "analytics", "reporting", "metrics", "dashboard", "monitoring"],
            "management": ["management", "leadership", "team", "project", "planning", "coordination"],
            "infrastructure": ["infrastructure", "deployment", "devops", "kubernetes", "docker"],
            "data": ["data", "database", "sql", "etl", "pipeline", "spark"],
            "python": ["python", "pytest", "flask", "django"],
            "detection": ["detection", "detection", "ids", "ips", "siem", "log"],
            "ir": ["incident response", "ir", "forensic", "recovery"],
        }

        for theme, keywords in theme_keywords.items():
            if any(kw in text_lower for kw in keywords):
                themes.append(theme)

        return ",".join(themes) if themes else "general"
