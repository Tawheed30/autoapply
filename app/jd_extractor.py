import re
import logging
from typing import List, Dict, Tuple
from collections import Counter

logger = logging.getLogger(__name__)


class JDExtractor:
    """Extract keywords and requirements from job descriptions locally (no API)."""

    # Common tech terms and tools
    TECH_KEYWORDS = {
        # Languages
        "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust", "ruby", "php",
        "sql", "bash", "shell", "groovy", "scala", "kotlin", "swift", "objective-c",

        # Cloud platforms
        "aws", "azure", "gcp", "google cloud", "digitalocean", "linode", "heroku",
        "ec2", "s3", "lambda", "rds", "dynamodb", "cloudformation", "terraform",

        # Databases
        "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
        "sqlite", "oracle", "sql server", "firestore", "dynamodb",

        # DevOps/Infrastructure
        "docker", "kubernetes", "k8s", "jenkins", "gitlab", "github actions", "circleci",
        "ansible", "puppet", "chef", "terraform", "vagrant", "prometheus", "grafana",
        "datadog", "newrelic", "splunk", "elk", "logstash", "kibana",

        # Frameworks
        "react", "vue", "angular", "django", "flask", "fastapi", "express", "spring",
        "node.js", "rails", "laravel", "asp.net", "next.js", "nuxt",

        # Testing/QA
        "pytest", "unittest", "jest", "mocha", "rspec", "selenium", "cypress",
        "jmeter", "locust", "testng", "junit",

        # Security
        "security", "siem", "ids", "ips", "vulnerability", "penetration testing", "pentest",
        "owasp", "cis", "nist", "iam", "sso", "oauth", "saml", "encryption",
        "ssl", "tls", "pki", "certs", "firewall", "vpn", "waf",

        # Data/Analytics
        "spark", "hadoop", "hive", "kafka", "airflow", "luigi", "dbt",
        "tableau", "power bi", "looker", "datadog", "mixpanel",

        # CI/CD
        "git", "github", "gitlab", "bitbucket", "jenkins", "travis", "circleci",
        "gitlab ci", "github actions", "azure pipelines",

        # Other
        "linux", "unix", "windows", "macos", "rest", "graphql", "soap", "grpc",
        "microservices", "monolith", "serverless", "api", "webhook", "queue",
        "rabbitmq", "activemq", "sqs", "pubsub", "event-driven",
    }

    # Skills and soft skills
    SKILL_KEYWORDS = {
        "communication", "leadership", "project management", "agile", "scrum", "kanban",
        "problem solving", "analytical", "troubleshooting", "debugging", "optimization",
        "design", "architecture", "mentoring", "training", "documentation",
    }

    # Experience/seniority indicators
    LEVEL_INDICATORS = {
        "senior": r"\b(senior|5\+|7\+|staff|principal|lead|5-|6-|7-)\b",
        "manager": r"\b(manager|director|vp|vice president)\b",
        "mid": r"\b(mid-level|mid\.?level|3-5|3-7|intermediate)\b",
        "junior": r"\b(entry-level|junior|0-2|0-3|graduate|entry)\b",
    }

    def __init__(self):
        self.all_keywords = self.TECH_KEYWORDS | self.SKILL_KEYWORDS
        logger.info(f"JDExtractor initialized with {len(self.all_keywords)} known keywords")

    def extract_keywords(self, jd_text: str, top_n: int = 15) -> List[str]:
        """Extract top keywords from job description text."""
        if not jd_text:
            return []

        # Normalize text
        text_lower = jd_text.lower()

        # Find matches in our keyword list
        found_keywords = []
        for keyword in self.all_keywords:
            # Check if keyword appears in text
            if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
                found_keywords.append(keyword)

        # If no keywords found, try looser matching
        if not found_keywords:
            words = re.findall(r'\b[a-z0-9\+\#\.\-_]+(?:\s+[a-z0-9\+\#\.\-_]+)?\b', text_lower)
            for word in words:
                word_clean = word.strip()
                if len(word_clean) > 3 and word_clean in text_lower:
                    found_keywords.append(word_clean)

        # Count and rank
        keyword_counts = Counter(found_keywords)
        top_keywords = [kw for kw, count in keyword_counts.most_common(top_n)]

        logger.info(f"Extracted {len(top_keywords)} top keywords from JD")
        return top_keywords

    def extract_requirements(self, jd_text: str) -> Dict[str, any]:
        """Extract structured requirements from JD."""
        text_lower = jd_text.lower()

        requirements = {
            "keywords": self.extract_keywords(jd_text),
            "years_required": self._extract_years(text_lower),
            "level": self._detect_level(text_lower),
            "must_have_skills": self._extract_must_haves(text_lower),
            "nice_to_have": self._extract_nice_to_haves(text_lower),
            "tools_mentioned": self._extract_tools(jd_text),
        }

        return requirements

    def _extract_years(self, text: str) -> int:
        """Extract required years of experience."""
        matches = re.findall(r'(\d+)\+?\s*(?:years|yrs?)', text)
        if matches:
            return int(matches[0])
        return 0

    def _detect_level(self, text: str) -> str:
        """Detect seniority level (junior, mid, senior, manager)."""
        for level, pattern in self.LEVEL_INDICATORS.items():
            if re.search(pattern, text):
                return level
        return "mid"

    def _extract_must_haves(self, text: str) -> List[str]:
        """Extract must-have skills."""
        must_haves = []

        # Look for "must have" / "required" sections
        sections = re.split(
            r'(must\s+have|required|mandatory|essential)',
            text,
            flags=re.IGNORECASE
        )

        if len(sections) > 1:
            content = sections[1:min(3, len(sections))]
            combined = " ".join(content)
            # Extract up to next section
            combined = combined[:500]
            keywords = self.extract_keywords(combined, top_n=10)
            must_haves = keywords

        return must_haves

    def _extract_nice_to_haves(self, text: str) -> List[str]:
        """Extract nice-to-have skills."""
        nice_to_haves = []

        sections = re.split(
            r'(nice\s+to\s+have|preferred|bonus|plus)',
            text,
            flags=re.IGNORECASE
        )

        if len(sections) > 1:
            content = sections[1:min(3, len(sections))]
            combined = " ".join(content)
            combined = combined[:500]
            keywords = self.extract_keywords(combined, top_n=10)
            nice_to_haves = keywords

        return nice_to_haves

    def _extract_tools(self, text: str) -> List[str]:
        """Extract specific tools/technologies mentioned."""
        tools = []
        for keyword in self.TECH_KEYWORDS:
            if keyword in text.lower():
                tools.append(keyword)
        return list(set(tools))[:15]

    def score_match(self, resume_skills: List[str], jd_keywords: List[str]) -> Dict[str, any]:
        """Score how well resume skills match JD keywords."""
        resume_set = set(skill.lower() for skill in resume_skills)
        jd_set = set(kw.lower() for kw in jd_keywords)

        matched = resume_set & jd_set
        missing = jd_set - resume_set

        score = len(matched) / len(jd_set) * 100 if jd_set else 0

        return {
            "score": round(score, 1),
            "matched_keywords": list(matched),
            "missing_keywords": list(missing),
            "match_count": len(matched),
            "total_keywords": len(jd_set),
        }
