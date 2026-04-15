"""
Tests for MailBot - Mail Reader Module
"""

import unittest
from unittest.mock import patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mail_reader import MailReader


class TestMailReader(unittest.TestCase):
    """Test MailReader class."""

    @patch.dict(os.environ, {
        "EMAIL_ADDRESS": "test@example.com",
        "EMAIL_PASSWORD": "testpass",
    })
    def setUp(self):
        self.reader = MailReader()

    @patch("mail_reader.imaplib.IMAP4_SSL")
    def test_connect(self, mock_imap):
        """Test IMAP connection."""
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn

        result = self.reader._connect()

        self.assertEqual(result, mock_conn)
        mock_conn.login.assert_called_once()

    @patch("mail_reader.imaplib.IMAP4_SSL")
    def test_fetch_inbox_empty(self, mock_imap):
        """Test fetching from an empty inbox."""
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.select.return_value = ("OK", [b"0"])
        mock_conn.search.return_value = ("OK", [b""])

        emails = self.reader.fetch_inbox(limit=5)

        self.assertEqual(emails, [])

    @patch("mail_reader.imaplib.IMAP4_SSL")
    def test_fetch_inbox_with_emails(self, mock_imap):
        """Test fetching emails from inbox."""
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.select.return_value = ("OK", [b"3"])
        mock_conn.search.return_value = ("OK", [b"1 2 3"])

        # Mock email data
        raw_email = (
            b"From: sender@example.com\r\n"
            b"To: test@example.com\r\n"
            b"Subject: Test Email\r\n"
            b"Date: Mon, 14 Apr 2026 10:00:00 +0000\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Hello, this is a test email."
        )
        mock_conn.fetch.return_value = ("OK", [(b"1", raw_email)])

        emails = self.reader.fetch_inbox(limit=3)

        self.assertEqual(len(emails), 3)
        self.assertEqual(emails[0]["subject"], "Test Email")
        self.assertEqual(emails[0]["from"], "sender@example.com")

    @patch("mail_reader.imaplib.IMAP4_SSL")
    def test_search_emails(self, mock_imap):
        """Test searching emails."""
        mock_conn = MagicMock()
        mock_imap.return_value = mock_conn
        mock_conn.select.return_value = ("OK", [b"5"])
        mock_conn.search.return_value = ("OK", [b"1 2"])

        raw_email = (
            b"From: sender@example.com\r\n"
            b"To: test@example.com\r\n"
            b"Subject: Meeting Notes\r\n"
            b"Date: Mon, 14 Apr 2026 10:00:00 +0000\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"Here are the meeting notes."
        )
        mock_conn.fetch.return_value = ("OK", [(b"1", raw_email)])

        emails = self.reader.search_emails(query="Meeting")

        self.assertGreater(len(emails), 0)

    def test_disconnect_without_connection(self):
        """Disconnecting without a connection should not raise."""
        self.reader.connection = None
        self.reader._disconnect()  # Should not raise


class TestMailReaderBodyExtraction(unittest.TestCase):
    """Test email body extraction."""

    @patch.dict(os.environ, {
        "EMAIL_ADDRESS": "test@example.com",
        "EMAIL_PASSWORD": "testpass",
    })
    def setUp(self):
        self.reader = MailReader()

    def test_extract_plain_text_body(self):
        """Test extracting plain text body from a simple email."""
        import email as email_lib

        raw = (
            b"From: test@example.com\r\n"
            b"Subject: Test\r\n"
            b"Content-Type: text/plain; charset=utf-8\r\n"
            b"\r\n"
            b"Plain text body."
        )
        msg = email_lib.message_from_bytes(raw)
        body = self.reader._extract_body(msg)

        self.assertEqual(body, "Plain text body.")

    def test_list_attachments_none(self):
        """Test listing attachments when there are none."""
        import email as email_lib

        raw = (
            b"From: test@example.com\r\n"
            b"Subject: Test\r\n"
            b"Content-Type: text/plain\r\n"
            b"\r\n"
            b"No attachments here."
        )
        msg = email_lib.message_from_bytes(raw)
        attachments = self.reader._list_attachments(msg)

        self.assertEqual(attachments, [])


if __name__ == "__main__":
    unittest.main()
