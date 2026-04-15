"""
MailBot - Email Sender Module
Handles sending plain text, HTML, and emails with attachments.
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import Config
from utils import setup_logger, validate_email
from template_engine import TemplateEngine


class MailSender:
    """Handles all email sending operations."""

    def __init__(self):
        self.config = Config
        self.logger = setup_logger("mailbot.sender")
        self.template_engine = TemplateEngine()

    def _connect(self):
        """Establish SMTP connection."""
        try:
            server = smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT)
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD)
            self.logger.info("SMTP connection established successfully.")
            return server
        except smtplib.SMTPAuthenticationError:
            self.logger.error("SMTP authentication failed. Check credentials.")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect to SMTP server: {e}")
            raise

    def send(self, to, subject, body, cc=None, bcc=None, attachments=None):
        """
        Send a plain text email.

        Args:
            to (str or list): Recipient email(s)
            subject (str): Email subject
            body (str): Email body (plain text)
            cc (str or list, optional): CC recipients
            bcc (str or list, optional): BCC recipients
            attachments (list, optional): List of file paths to attach
        """
        if isinstance(to, str):
            to = [to]
        if cc and isinstance(cc, str):
            cc = [cc]
        if bcc and isinstance(bcc, str):
            bcc = [bcc]

        # Validate recipients
        all_recipients = to + (cc or []) + (bcc or [])
        for email in all_recipients:
            if not validate_email(email):
                self.logger.error(f"Invalid email address: {email}")
                raise ValueError(f"Invalid email address: {email}")

        msg = MIMEMultipart()
        msg["From"] = self.config.EMAIL_ADDRESS
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        msg.attach(MIMEText(body, "plain"))

        # Add attachments
        if attachments:
            for filepath in attachments:
                self._attach_file(msg, filepath)

        # Send
        try:
            server = self._connect()
            server.sendmail(self.config.EMAIL_ADDRESS, all_recipients, msg.as_string())
            server.quit()
            self.logger.info(f"Email sent to {', '.join(to)} | Subject: {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send email: {e}")
            raise

    def send_html(self, to, subject, html_body=None, template=None, context=None,
                  cc=None, bcc=None, attachments=None):
        """
        Send an HTML email, optionally using a template.

        Args:
            to (str or list): Recipient email(s)
            subject (str): Email subject
            html_body (str, optional): Raw HTML body
            template (str, optional): Template name (without .html)
            context (dict, optional): Template variables
            cc (str or list, optional): CC recipients
            bcc (str or list, optional): BCC recipients
            attachments (list, optional): List of file paths to attach
        """
        if isinstance(to, str):
            to = [to]
        if cc and isinstance(cc, str):
            cc = [cc]
        if bcc and isinstance(bcc, str):
            bcc = [bcc]

        # Render template if provided
        if template:
            html_body = self.template_engine.render(template, context or {})
        elif not html_body:
            raise ValueError("Either html_body or template must be provided.")

        msg = MIMEMultipart("alternative")
        msg["From"] = self.config.EMAIL_ADDRESS
        msg["To"] = ", ".join(to)
        msg["Subject"] = subject

        if cc:
            msg["Cc"] = ", ".join(cc)

        # Attach HTML
        msg.attach(MIMEText(html_body, "html"))

        # Add attachments
        if attachments:
            for filepath in attachments:
                self._attach_file(msg, filepath)

        # Send
        all_recipients = to + (cc or []) + (bcc or [])
        try:
            server = self._connect()
            server.sendmail(self.config.EMAIL_ADDRESS, all_recipients, msg.as_string())
            server.quit()
            self.logger.info(f"HTML email sent to {', '.join(to)} | Subject: {subject}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to send HTML email: {e}")
            raise

    def _attach_file(self, msg, filepath):
        """Attach a file to the email message."""
        if not os.path.isfile(filepath):
            self.logger.warning(f"Attachment not found: {filepath}")
            raise FileNotFoundError(f"Attachment not found: {filepath}")

        filename = os.path.basename(filepath)
        with open(filepath, "rb") as f:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f'attachment; filename="{filename}"'
            )
            msg.attach(part)
            self.logger.debug(f"Attached file: {filename}")

    def send_bulk(self, recipients, subject, body, is_html=False):
        """
        Send the same email to multiple recipients individually.

        Args:
            recipients (list): List of email addresses
            subject (str): Email subject
            body (str): Email body
            is_html (bool): Whether the body is HTML
        """
        results = {"success": [], "failed": []}

        for recipient in recipients:
            try:
                if is_html:
                    self.send_html(to=recipient, subject=subject, html_body=body)
                else:
                    self.send(to=recipient, subject=subject, body=body)
                results["success"].append(recipient)
            except Exception as e:
                self.logger.error(f"Failed to send to {recipient}: {e}")
                results["failed"].append({"email": recipient, "error": str(e)})

        self.logger.info(
            f"Bulk send complete: {len(results['success'])} sent, "
            f"{len(results['failed'])} failed"
        )
        return results
