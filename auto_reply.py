"""
MailBot - Auto Reply Module
Automatically replies to incoming emails based on configurable rules.
"""

import time
import threading
from mail_reader import MailReader
from mail_sender import MailSender
from config import Config
from utils import setup_logger


class AutoReply:
    """Handles automatic email replies based on rules."""

    def __init__(self):
        self.reader = MailReader()
        self.sender = MailSender()
        self.config = Config
        self.logger = setup_logger("mailbot.autoreply")
        self.rules = []
        self.replied_ids = set()
        self._running = False
        self._thread = None

    def add_rule(self, name, condition, reply_subject=None, reply_body=None,
                 reply_template=None, reply_context=None):
        """
        Add an auto-reply rule.

        Args:
            name (str): Rule name
            condition (callable): Function that takes an email dict, returns True/False
            reply_subject (str, optional): Reply subject (default: "Re: {original_subject}")
            reply_body (str, optional): Reply body text
            reply_template (str, optional): Template name for HTML reply
            reply_context (dict, optional): Template context
        """
        rule = {
            "name": name,
            "condition": condition,
            "reply_subject": reply_subject,
            "reply_body": reply_body,
            "reply_template": reply_template,
            "reply_context": reply_context,
        }
        self.rules.append(rule)
        self.logger.info(f"Auto-reply rule added: {name}")

    def add_keyword_rule(self, name, keyword, reply_body, case_sensitive=False):
        """
        Add a rule that triggers when a keyword is found in the subject or body.

        Args:
            name (str): Rule name
            keyword (str): Keyword to match
            reply_body (str): Reply body text
            case_sensitive (bool): Whether matching is case-sensitive
        """
        def condition(email_data):
            subject = email_data.get("subject", "")
            body = email_data.get("body", "")
            text = f"{subject} {body}"
            if not case_sensitive:
                text = text.lower()
                kw = keyword.lower()
            else:
                kw = keyword
            return kw in text

        self.add_rule(name=name, condition=condition, reply_body=reply_body)

    def add_sender_rule(self, name, sender_email, reply_body):
        """
        Add a rule that triggers for emails from a specific sender.

        Args:
            name (str): Rule name
            sender_email (str): Sender email to match
            reply_body (str): Reply body text
        """
        def condition(email_data):
            return sender_email.lower() in email_data.get("from", "").lower()

        self.add_rule(name=name, condition=condition, reply_body=reply_body)

    def _process_email(self, email_data):
        """Check an email against all rules and send reply if matched."""
        email_id = email_data.get("id")

        if email_id in self.replied_ids:
            return

        # Skip own emails
        if self.config.EMAIL_ADDRESS.lower() in email_data.get("from", "").lower():
            return

        for rule in self.rules:
            try:
                if rule["condition"](email_data):
                    subject = rule["reply_subject"] or f"Re: {email_data['subject']}"
                    sender = email_data["from"]

                    # Extract just the email address
                    if "<" in sender and ">" in sender:
                        sender = sender.split("<")[1].split(">")[0]

                    if rule["reply_template"]:
                        self.sender.send_html(
                            to=sender,
                            subject=subject,
                            template=rule["reply_template"],
                            context=rule["reply_context"] or {},
                        )
                    else:
                        body = rule["reply_body"] or self.config.AUTO_REPLY_MESSAGE
                        self.sender.send(
                            to=sender,
                            subject=subject,
                            body=body,
                        )

                    self.replied_ids.add(email_id)
                    self.logger.info(
                        f"Auto-replied to {sender} | Rule: {rule['name']} | "
                        f"Subject: {subject}"
                    )
                    break  # Only apply first matching rule

            except Exception as e:
                self.logger.error(f"Auto-reply failed for rule '{rule['name']}': {e}")

    def check_and_reply(self, limit=5):
        """
        Check for new unread emails and apply auto-reply rules.

        Args:
            limit (int): Number of recent unread emails to check
        """
        try:
            emails = self.reader.fetch_inbox(limit=limit, unread_only=True)
            for email_data in emails:
                self._process_email(email_data)
        except Exception as e:
            self.logger.error(f"Error checking emails: {e}")

    def start(self, check_interval=60):
        """
        Start auto-reply in a background thread.

        Args:
            check_interval (int): Seconds between inbox checks
        """
        if not self.rules and not self.config.AUTO_REPLY_ENABLED:
            self.logger.warning("No auto-reply rules configured and auto-reply is disabled.")
            return

        # If no custom rules, add a default reply-all rule
        if not self.rules and self.config.AUTO_REPLY_ENABLED:
            self.add_rule(
                name="default",
                condition=lambda e: True,
                reply_body=self.config.AUTO_REPLY_MESSAGE,
            )

        self._running = True
        self.logger.info(f"Auto-reply started (checking every {check_interval}s)")

        def run():
            while self._running:
                self.check_and_reply()
                time.sleep(check_interval)

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop auto-reply."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
        self.logger.info("Auto-reply stopped.")

    def list_rules(self):
        """Return list of configured rules."""
        return [{"name": r["name"]} for r in self.rules]
