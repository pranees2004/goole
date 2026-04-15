"""
Tests for MailBot - Mail Sender Module
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mail_sender import MailSender
from utils import validate_email


class TestValidateEmail(unittest.TestCase):
    """Test email validation utility."""

    def test_valid_emails(self):
        valid = [
            "test@example.com",
            "user.name@domain.co",
            "user+tag@example.org",
            "first.last@sub.domain.com",
        ]
        for email in valid:
            self.assertTrue(validate_email(email), f"{email} should be valid")

    def test_invalid_emails(self):
        invalid = [
            "notanemail",
            "@domain.com",
            "user@",
            "user@.com",
            "",
            "user @domain.com",
        ]
        for email in invalid:
            self.assertFalse(validate_email(email), f"{email} should be invalid")


class TestMailSender(unittest.TestCase):
    """Test MailSender class."""

    @patch.dict(os.environ, {
        "EMAIL_ADDRESS": "test@example.com",
        "EMAIL_PASSWORD": "testpass",
    })
    def setUp(self):
        self.sender = MailSender()

    def test_invalid_recipient_raises_error(self):
        """Sending to an invalid email should raise ValueError."""
        with self.assertRaises(ValueError):
            self.sender.send(
                to="invalid-email",
                subject="Test",
                body="Test body"
            )

    @patch("mail_sender.smtplib.SMTP")
    def test_send_plain_email(self, mock_smtp):
        """Test sending a plain text email."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = self.sender.send(
            to="recipient@example.com",
            subject="Test Subject",
            body="Test body content"
        )

        self.assertTrue(result)
        mock_server.sendmail.assert_called_once()
        mock_server.quit.assert_called_once()

    @patch("mail_sender.smtplib.SMTP")
    def test_send_to_multiple_recipients(self, mock_smtp):
        """Test sending to multiple recipients."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        recipients = ["user1@example.com", "user2@example.com"]
        result = self.sender.send(
            to=recipients,
            subject="Bulk Test",
            body="Test body"
        )

        self.assertTrue(result)
        call_args = mock_server.sendmail.call_args
        self.assertEqual(len(call_args[0][1]), 2)

    def test_attachment_not_found(self):
        """Attaching a non-existent file should raise FileNotFoundError."""
        with self.assertRaises(FileNotFoundError):
            self.sender.send(
                to="recipient@example.com",
                subject="Test",
                body="Test",
                attachments=["/nonexistent/file.txt"]
            )

    @patch("mail_sender.smtplib.SMTP")
    def test_send_html_email(self, mock_smtp):
        """Test sending an HTML email."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        result = self.sender.send_html(
            to="recipient@example.com",
            subject="HTML Test",
            html_body="<h1>Hello</h1>"
        )

        self.assertTrue(result)

    def test_send_html_without_body_or_template(self):
        """send_html should raise ValueError if no body or template given."""
        with self.assertRaises(ValueError):
            self.sender.send_html(
                to="recipient@example.com",
                subject="Test",
            )


if __name__ == "__main__":
    unittest.main()
