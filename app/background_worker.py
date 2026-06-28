import logging
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
from app.database import Database
from app.job_queue import JobQueueManager
from app.tracker import TrackerManager
from app.resume_parser import ResumeParser
from app.experience_bank import ExperienceBank
from app.jd_extractor import JDExtractor
from app.resume_tailor import ResumeTailor
from app.question_drafter import QuestionDrafter
from app.cover_letter_generator import CoverLetterGenerator
from app.config import Config

logger = logging.getLogger(__name__)


class BackgroundWorker:
    def __init__(self, db: Database, config: Config, api_key: str):
        self.db = db
        self.config = config
        self.api_key = api_key
        self.queue_manager = JobQueueManager(db)
        self.tracker_manager = TrackerManager(db)
        self.extractor = JDExtractor()

    def process_queued_jobs(self):
        """Main worker function: processes all queued jobs."""
        logger.info("Starting background worker...")
        self.db.log_activity("worker_started", "background_worker", "Processing queued jobs")

        queued_jobs = self.queue_manager.get_queued_jobs()
        logger.info(f"Found {len(queued_jobs)} queued jobs")

        for job in queued_jobs:
            try:
                self._process_job(job)
            except Exception as e:
                logger.error(f"Error processing job {job['id']}: {str(e)}", exc_info=True)
                self.queue_manager.update_job_status(
                    job['id'],
                    status='failed',
                    error_message=str(e)
                )
                self.db.log_activity(
                    "job_failed",
                    f"job_id:{job['id']}",
                    f"error:{str(e)}",
                    "error"
                )

        logger.info("Background worker completed")
        self.db.log_activity("worker_completed", "background_worker", "Finished processing jobs")

    def _process_job(self, job: dict):
        """Process a single queued job."""
        job_id = job['id']
        logger.info(f"Processing job {job_id}: {job.get('company', 'Unknown')}")

        # Step 1: Get JD text
        jd_text = job.get('jd_text') or self._fetch_jd_url(job.get('jd_url'))
        if not jd_text:
            raise ValueError("Could not retrieve JD text")

        # Step 2: Extract JD keywords and requirements
        jd_keywords = self.extractor.extract_keywords(jd_text, top_n=15)
        jd_requirements = self.extractor.extract_requirements(jd_text)
        logger.info(f"Extracted {len(jd_keywords)} keywords from JD")

        # Step 3: Match resume skills against JD
        parser = ResumeParser(self._get_master_resume_path())
        contact = parser.extract_contact_info()
        sections = parser.parse_resume()

        # Get all skills from experience bank and resume
        all_skills = sections.get('skills', [])
        bank = ExperienceBank(self.db)
        bank_skills = [e['content'] for e in bank.get_entries_by_category('skill')]
        all_skills.extend(bank_skills)

        match_report = self.extractor.score_match(all_skills, jd_keywords)
        logger.info(f"Match score: {match_report['score']}% ({match_report['match_count']}/{match_report['total_keywords']})")

        # Step 4: Tailor resume
        output_dir = Path(self.config.get("data.tailored_resume_dir", "data/tailored"))
        output_dir.mkdir(parents=True, exist_ok=True)

        company = job.get('company', 'Unknown')
        role = job.get('role', 'Unknown')
        output_filename = f"{company}_{role}_resume.docx".replace(" ", "_").replace("/", "_")
        output_path = str(output_dir / output_filename)

        tailor = ResumeTailor(api_key=self.api_key, model=self.config.get("anthropic.models.resume_tailor", "claude-sonnet-4-6"))
        tailored_path, changes = tailor.tailor_resume(
            self._get_master_resume_path(),
            jd_text,
            jd_keywords,
            match_report,
            output_path,
        )

        logger.info(f"Resume tailored: {len(changes)} changes made")

        # Step 5: Save diff report
        diff_path = str(output_dir / f"{Path(output_filename).stem}_diff.md")
        tailor.save_diff_report(diff_path)

        # Step 6: Draft questions and answers
        parser = ResumeParser(self._get_master_resume_path())
        resume_data = parser.parse_resume()
        bank = ExperienceBank(self.db)

        drafter = QuestionDrafter(self.api_key, self.config.get("anthropic.models.bulk_draft", "claude-haiku-4-5"))
        questions = drafter.draft_questions(job_id, jd_text, resume_data, bank)
        logger.info(f"Drafted {len(questions)} questions for job {job_id}")

        # Step 7: Generate cover letter
        gen = CoverLetterGenerator(self.api_key, self.config.get("anthropic.models.cover_letter", "claude-sonnet-4-6"))
        cover_letter_text = gen.generate_cover_letter(
            company=company or "Unknown",
            role=role or "Unknown",
            jd_text=jd_text,
            resume_data=resume_data,
            bank=bank
        )

        # Insert cover letter into database
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cover_letters (job_id, company, role, cover_letter_text)
            VALUES (?, ?, ?, ?)
        """, (job_id, company or "Unknown", role or "Unknown", cover_letter_text))
        conn.commit()
        conn.close()
        logger.info(f"Generated cover letter for job {job_id}")

        # Step 8: Create tracker entry
        tracker_entry_id = self.tracker_manager.create_entry(
            company=company or "Unknown",
            role=role or "Unknown",
            location=job.get('location'),
            platform=None,  # To be filled in by user
            region=None,  # To be filled in by user
            jd_url=job.get('jd_url'),
            status='staged',
            notes=None,
            resume_version_id=None,  # Can be set when user approves
        )

        # Step 9: Update job queue status
        result = {
            "resume_path": tailored_path,
            "diff_path": diff_path,
            "match_report": match_report,
            "keywords": jd_keywords,
            "tracker_entry_id": tracker_entry_id,
        }

        self.queue_manager.update_job_status(
            job_id,
            status='staged',
            result=result,
        )

        # Step 8: Log success
        self.db.log_activity(
            "resume_tailored",
            f"job_id:{job_id}, tracker_id:{tracker_entry_id}",
            f"company:{company}, role:{role}, match_score:{match_report['score']}%",
            "success"
        )

        logger.info(f"Job {job_id} processed successfully, tracker entry {tracker_entry_id} created")

    def _get_master_resume_path(self) -> str:
        """Get the path to the master resume."""
        master_dir = self.config.get("data.resume_dir", "data/resumes")
        master_path = os.path.join(master_dir, "master.docx")
        if not os.path.exists(master_path):
            raise FileNotFoundError(f"Master resume not found: {master_path}")
        return master_path

    def _fetch_jd_url(self, url: Optional[str]) -> Optional[str]:
        """Fetch JD text from URL (placeholder)."""
        if not url:
            return None

        try:
            import requests
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            # For now, return the response text
            # In production, you'd parse HTML/PDF to extract the job description
            return response.text[:5000]  # First 5000 chars
        except Exception as e:
            logger.error(f"Error fetching JD from URL: {str(e)}")
            return None
