"""
MailBot - Email Scheduler Module
Schedule emails to be sent at specific times.
"""

import time
import threading
from datetime import datetime
import schedule
from mail_sender import MailSender
from utils import setup_logger


class MailScheduler:
    """Handles scheduling emails for future delivery."""

    def __init__(self):
        self.sender = MailSender()
        self.logger = setup_logger("mailbot.scheduler")
        self.scheduled_jobs = []
        self._running = False
        self._thread = None

    def schedule(self, to, subject, body, send_at, is_html=False,
                 attachments=None, template=None, context=None):
        """
        Schedule an email to be sent at a specific time.

        Args:
            to (str or list): Recipient(s)
            subject (str): Email subject
            body (str): Email body
            send_at (str): Send time in "YYYY-MM-DD HH:MM:SS" format
            is_html (bool): Whether the body is HTML
            attachments (list, optional): File paths to attach
            template (str, optional): Template name for HTML emails
            context (dict, optional): Template context variables
        """
        send_time = datetime.strptime(send_at, "%Y-%m-%d %H:%M:%S")

        if send_time <= datetime.now():
            self.logger.warning(f"Scheduled time {send_at} is in the past.")
            raise ValueError("Scheduled time must be in the future.")

        job = {
            "to": to,
            "subject": subject,
            "body": body,
            "send_at": send_time,
            "is_html": is_html,
            "attachments": attachments,
            "template": template,
            "context": context,
            "status": "pending",
        }

        self.scheduled_jobs.append(job)
        self.logger.info(f"Email scheduled for {send_at} | To: {to} | Subject: {subject}")
        return job

    def schedule_recurring(self, to, subject, body, interval="daily", at_time="09:00",
                           is_html=False):
        """
        Schedule a recurring email.

        Args:
            to (str): Recipient
            subject (str): Email subject
            body (str): Email body
            interval (str): "daily", "hourly", "weekly"
            at_time (str): Time in "HH:MM" format (for daily/weekly)
            is_html (bool): Whether the body is HTML
        """
        def send_job():
            try:
                if is_html:
                    self.sender.send_html(to=to, subject=subject, html_body=body)
                else:
                    self.sender.send(to=to, subject=subject, body=body)
                self.logger.info(f"Recurring email sent to {to}")
            except Exception as e:
                self.logger.error(f"Recurring email failed: {e}")

        if interval == "daily":
            schedule.every().day.at(at_time).do(send_job)
        elif interval == "hourly":
            schedule.every().hour.do(send_job)
        elif interval == "weekly":
            schedule.every().week.at(at_time).do(send_job)
        else:
            raise ValueError(f"Invalid interval: {interval}. Use 'daily', 'hourly', or 'weekly'.")

        self.logger.info(f"Recurring email set: {interval} at {at_time} | To: {to}")

    def _process_scheduled(self):
        """Check and send any due scheduled emails."""
        now = datetime.now()

        for job in self.scheduled_jobs:
            if job["status"] == "pending" and now >= job["send_at"]:
                try:
                    if job["template"]:
                        self.sender.send_html(
                            to=job["to"],
                            subject=job["subject"],
                            template=job["template"],
                            context=job["context"],
                            attachments=job["attachments"],
                        )
                    elif job["is_html"]:
                        self.sender.send_html(
                            to=job["to"],
                            subject=job["subject"],
                            html_body=job["body"],
                            attachments=job["attachments"],
                        )
                    else:
                        self.sender.send(
                            to=job["to"],
                            subject=job["subject"],
                            body=job["body"],
                            attachments=job["attachments"],
                        )
                    job["status"] = "sent"
                    self.logger.info(f"Scheduled email sent to {job['to']}")
                except Exception as e:
                    job["status"] = "failed"
                    self.logger.error(f"Scheduled email failed: {e}")

    def start(self, check_interval=30):
        """
        Start the scheduler in a background thread.

        Args:
            check_interval (int): Seconds between checks
        """
        self._running = True
        self.logger.info("Scheduler started.")

        def run():
            while self._running:
                self._process_scheduled()
                schedule.run_pending()
                time.sleep(check_interval)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Scheduler stopped.")

    def get_pending_jobs(self):
        """Return list of pending scheduled jobs."""
        return [j for j in self.scheduled_jobs if j["status"] == "pending"]

    def cancel_all(self):
        """Cancel all pending scheduled jobs."""
        for job in self.scheduled_jobs:
            if job["status"] == "pending":
                job["status"] = "cancelled"
        schedule.clear()
        self.logger.info("All scheduled jobs cancelled.")
