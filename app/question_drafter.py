import logging
import re
from typing import Dict, List, Optional, Tuple
from app.experience_bank import ExperienceBank
from app.database import Database
from anthropic import Anthropic

logger = logging.getLogger(__name__)


class QuestionDrafter:
    """Draft answers to application questions based on resume and JD."""

    # Typical application questions
    TYPICAL_QUESTIONS = [
        "Why do you want to work for [company]?",
        "Why are you interested in this [role]?",
        "Describe a time you handled a challenging situation.",
        "Tell us about a project you're proud of.",
        "What's your experience with [technology]?",
        "How do you handle disagreement with team members?",
        "Describe your leadership experience.",
    ]

    # Sensitive question patterns (Phase 3b)
    SENSITIVE_PATTERNS = {
        "work_auth": [
            r"sponsorship|visa|work.*auth|legal.*right|right.*work|require.*sponsor",
            r"can you work in|authorized.*work|need.*sponsorship"
        ],
        "salary": [
            r"salary.*expect|expectation|current.*salary|compensation|pay.*expect",
            r"how much.*earn|salary.*requirement"
        ],
        "notice": [
            r"notice.*period|how much notice|available.*start|when.*available",
            r"current.*notice|notice.*require"
        ],
        "relocation": [
            r"relocate|willing.*move|relocat|move to|based in",
            r"commute|location.*work"
        ]
    }

    # Region-specific hints
    REGION_HINTS = {
        "uae": "Sponsorship typically required in UAE. Confirm your visa/sponsorship status.",
        "middle_east": "Sponsorship often required in this region. Confirm your status.",
        "singapore": "Employment Pass salary thresholds may apply. Consider your salary expectations.",
        "malaysia": "Employment Pass category may apply. Note any specific preferences.",
        "europe": "Work rights vary by country. Blue Card eligibility may apply in some EU countries.",
        "default": "This question requires your specific input. Leave blank until you're ready to answer."
    }

    def __init__(self, db: Database, api_key: str):
        self.db = db
        self.client = Anthropic(api_key=api_key)
        self.bank = ExperienceBank(db)

    def draft_answers(
        self,
        job_id: int,
        jd_text: str,
        jd_keywords: List[str],
        company: str,
        role: str,
        region: Optional[str] = None
    ) -> List[Dict]:
        """Draft answers for typical application questions."""
        logger.info(f"Drafting answers for job {job_id}: {company} - {role}")

        # Get all experience bank entries
        all_entries = self.bank.get_all_entries()
        resume_content = self._format_resume_content(all_entries)

        drafted_answers = []

        # Generate custom questions based on JD
        custom_questions = self._generate_custom_questions(jd_text, company, role)

        for question in custom_questions:
            try:
                answer_data = self._draft_answer(
                    question,
                    jd_text,
                    resume_content,
                    company,
                    role,
                    jd_keywords
                )

                # Check if sensitive
                is_sensitive, question_type, hint = self._detect_sensitive(question, region)
                if is_sensitive:
                    answer_data["flagged"] = True
                    answer_data["question_type"] = question_type
                    answer_data["region_hint"] = hint
                    answer_data["answer"] = None  # Never auto-answer sensitive questions
                    logger.info(f"Flagged sensitive question: {question_type}")

                drafted_answers.append(answer_data)

            except Exception as e:
                logger.error(f"Error drafting answer for question '{question}': {e}")
                drafted_answers.append({
                    "question": question,
                    "answer": None,
                    "confidence": "low",
                    "source_bullets": [],
                    "error": str(e)
                })

        logger.info(f"Drafted {len(drafted_answers)} answers for job {job_id}")
        return drafted_answers

    def _generate_custom_questions(self, jd_text: str, company: str, role: str) -> List[str]:
        """Generate custom questions based on JD content."""
        questions = [
            f"Why do you want to work for {company}?",
            f"Why are you interested in this {role} role?",
        ]

        # Add technology-specific questions
        tech_keywords = re.findall(r'\b(Python|Go|Java|JavaScript|AWS|Docker|Kubernetes|React|Vue)\b', jd_text, re.I)
        for tech in set(tech_keywords[:3]):
            questions.append(f"What's your experience with {tech}?")

        # Add behavioral questions
        if "lead" in jd_text.lower() or "team" in jd_text.lower():
            questions.append("Describe your experience leading or working with teams.")

        if "architect" in jd_text.lower() or "design" in jd_text.lower():
            questions.append("Tell us about a system or architecture you designed.")

        if "urgent" in jd_text.lower() or "deadline" in jd_text.lower():
            questions.append("Describe a time you delivered under a tight deadline.")

        return questions[:5]  # Return top 5 questions

    def _draft_answer(
        self,
        question: str,
        jd_text: str,
        resume_content: str,
        company: str,
        role: str,
        jd_keywords: List[str]
    ) -> Dict:
        """Draft a single answer using Claude."""
        prompt = f"""You are helping someone tailor their application answers.
Generate a concise, first-person answer (2-3 sentences) to this question based ONLY on the provided resume content.

**Question:** {question}

**Company/Role Context:** {company} - {role}

**Key JD Keywords:** {', '.join(jd_keywords[:5])}

**Resume Content (use ONLY what's provided):**
{resume_content}

**Requirements:**
- Answer must be grounded ONLY in the resume content provided
- Never fabricate or invent experience
- Keep to 2-3 sentences, conversational tone
- Start with first person (I, my, we)
- If you can't answer well from the resume, say "Not well-matched to my experience" but still provide the best match

Respond with ONLY the answer text, no explanation."""

        try:
            message = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            answer_text = message.content[0].text.strip()

            # Assess confidence based on match
            confidence = self._assess_confidence(answer_text, jd_keywords)

            return {
                "question": question,
                "answer": answer_text,
                "confidence": confidence,
                "source_bullets": [],  # Would be populated from experience bank matching
                "flagged": False
            }

        except Exception as e:
            logger.error(f"Error calling Claude for answer: {e}")
            raise

    def _format_resume_content(self, entries: List[Dict]) -> str:
        """Format experience bank entries as resume text."""
        content = "Resume Content:\n\n"

        # Group by category
        by_category = {}
        for entry in entries:
            cat = entry.get("category", "other")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(entry["content"])

        for category, items in by_category.items():
            content += f"**{category.capitalize()}:**\n"
            for item in items[:10]:  # Limit to 10 items per category
                content += f"- {item}\n"
            content += "\n"

        return content

    def _assess_confidence(self, answer: str, jd_keywords: List[str]) -> str:
        """Assess confidence level of the answer."""
        # Check if answer contains "not well-matched" or similar
        if "not well-matched" in answer.lower() or "limited" in answer.lower():
            return "low"

        # Check keyword overlap
        answer_lower = answer.lower()
        keyword_matches = sum(1 for kw in jd_keywords if kw.lower() in answer_lower)

        if keyword_matches >= 3:
            return "high"
        elif keyword_matches >= 1:
            return "medium"
        else:
            return "low"

    def _detect_sensitive(self, question: str, region: Optional[str] = None) -> Tuple[bool, Optional[str], Optional[str]]:
        """Detect if a question is sensitive and return region-specific hint."""
        question_lower = question.lower()

        for question_type, patterns in self.SENSITIVE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, question_lower, re.IGNORECASE):
                    # Get region hint
                    region_key = (region or "default").lower()
                    if region_key in self.REGION_HINTS:
                        hint = self.REGION_HINTS[region_key]
                    else:
                        hint = self.REGION_HINTS["default"]

                    return True, question_type, hint

        return False, None, None
