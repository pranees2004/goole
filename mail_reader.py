"""
MailBot - Email Reader Module
Handles fetching and parsing emails from inbox via IMAP.
"""

import imaplib
import email
from email.header import decode_header
from datetime import datetime
from config import Config
from utils import setup_logger, sanitize_filename
import os


class MailReader:
    """Handles all email reading/fetching operations."""

    def __init__(self):
        self.config = Config
        self.logger = setup_logger("mailbot.reader")
        self.connection = None

    def _connect(self):
        """Establish IMAP connection."""
        try:
            self.connection = imaplib.IMAP4_SSL(
                self.config.IMAP_HOST, self.config.IMAP_PORT
            )
            self.connection.login(
                self.config.EMAIL_ADDRESS, self.config.EMAIL_PASSWORD
            )
            self.logger.info("IMAP connection established successfully.")
            return self.connection
        except imaplib.IMAP4.error as e:
            self.logger.error(f"IMAP authentication failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Failed to connect to IMAP server: {e}")
            raise

    def _disconnect(self):
        """Close IMAP connection."""
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
                self.logger.debug("IMAP connection closed.")
            except Exception:
                pass

    def fetch_inbox(self, limit=10, folder="INBOX", unread_only=False):
        """
        Fetch emails from the inbox.

        Args:
            limit (int): Maximum number of emails to fetch
            folder (str): Mailbox folder to read from
            unread_only (bool): If True, fetch only unread emails

        Returns:
            list: List of parsed email dictionaries
        """
        conn = self._connect()
        conn.select(folder)

        search_criteria = "UNSEEN" if unread_only else "ALL"
        status, messages = conn.search(None, search_criteria)

        if status != "OK":
            self.logger.error("Failed to search emails.")
            self._disconnect()
            return []

        email_ids = messages[0].split()
        email_ids = email_ids[-limit:]  # Get the latest N emails
        email_ids.reverse()  # Newest first

        emails = []
        for eid in email_ids:
            try:
                parsed = self._fetch_email(conn, eid)
                if parsed:
                    emails.append(parsed)
            except Exception as e:
                self.logger.error(f"Error fetching email {eid}: {e}")

        self._disconnect()
        self.logger.info(f"Fetched {len(emails)} emails from {folder}.")
        return emails

    def _fetch_email(self, conn, email_id):
        """Fetch and parse a single email by ID."""
        status, data = conn.fetch(email_id, "(RFC822)")
        if status != "OK":
            return None

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)

        # Decode subject
        subject, encoding = decode_header(msg["Subject"])[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="replace")

        # Decode sender
        from_addr = msg.get("From", "Unknown")

        # Parse date
        date_str = msg.get("Date", "")
        try:
            date = email.utils.parsedate_to_datetime(date_str)
        except Exception:
            date = None

        # Extract body
        body = self._extract_body(msg)

        # Extract attachments info
        attachments = self._list_attachments(msg)

        return {
            "id": email_id.decode(),
            "from": from_addr,
            "to": msg.get("To", ""),
            "subject": subject,
            "date": date.isoformat() if date else date_str,
            "body": body,
            "attachments": attachments,
        }

    def _extract_body(self, msg):
        """Extract the email body (prefers plain text)."""
        body = ""

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in content_disposition:
                    continue

                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                    except Exception:
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )
                    break
                elif content_type == "text/html" and not body:
                    try:
                        body = part.get_payload(decode=True).decode(
                            part.get_content_charset() or "utf-8", errors="replace"
                        )
                    except Exception:
                        body = part.get_payload(decode=True).decode(
                            "utf-8", errors="replace"
                        )
        else:
            try:
                body = msg.get_payload(decode=True).decode(
                    msg.get_content_charset() or "utf-8", errors="replace"
                )
            except Exception:
                body = msg.get_payload(decode=True).decode("utf-8", errors="replace")

        return body.strip()

    def _list_attachments(self, msg):
        """List attachment filenames in the email."""
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        fname, enc = decode_header(filename)[0]
                        if isinstance(fname, bytes):
                            fname = fname.decode(enc or "utf-8", errors="replace")
                        attachments.append(fname)

        return attachments

    def download_attachments(self, email_id, save_dir="downloads", folder="INBOX"):
        """
        Download attachments from a specific email.

        Args:
            email_id (str): Email ID to download attachments from
            save_dir (str): Directory to save attachments
            folder (str): Mailbox folder

        Returns:
            list: List of saved file paths
        """
        os.makedirs(save_dir, exist_ok=True)
        conn = self._connect()
        conn.select(folder)

        status, data = conn.fetch(email_id.encode(), "(RFC822)")
        if status != "OK":
            self._disconnect()
            return []

        raw_email = data[0][1]
        msg = email.message_from_bytes(raw_email)
        saved_files = []

        if msg.is_multipart():
            for part in msg.walk():
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" in content_disposition:
                    filename = part.get_filename()
                    if filename:
                        fname, enc = decode_header(filename)[0]
                        if isinstance(fname, bytes):
                            fname = fname.decode(enc or "utf-8", errors="replace")
                        fname = sanitize_filename(fname)
                        filepath = os.path.join(save_dir, fname)

                        with open(filepath, "wb") as f:
                            f.write(part.get_payload(decode=True))

                        saved_files.append(filepath)
                        self.logger.info(f"Downloaded attachment: {fname}")

        self._disconnect()
        return saved_files

    def search_emails(self, query, folder="INBOX", limit=20):
        """
        Search emails by subject or sender.

        Args:
            query (str): Search query
            folder (str): Mailbox folder
            limit (int): Max results

        Returns:
            list: Matching emails
        """
        conn = self._connect()
        conn.select(folder)

        # Search by subject
        status, msg_ids_subj = conn.search(None, f'SUBJECT "{query}"')
        # Search by sender
        status2, msg_ids_from = conn.search(None, f'FROM "{query}"')

        all_ids = set(msg_ids_subj[0].split() + msg_ids_from[0].split())
        all_ids = sorted(all_ids, reverse=True)[:limit]

        emails = []
        for eid in all_ids:
            try:
                parsed = self._fetch_email(conn, eid)
                if parsed:
                    emails.append(parsed)
            except Exception as e:
                self.logger.error(f"Error fetching email {eid}: {e}")

        self._disconnect()
        self.logger.info(f"Search '{query}' returned {len(emails)} results.")
        return emails
