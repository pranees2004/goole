# 📧 MailBot

A powerful, automated email bot built with Python. MailBot can send, receive, and automate email tasks with ease.

## Features

- 📤 **Send Emails** — Send plain text and HTML emails with attachments
- 📥 **Read Emails** — Fetch and parse incoming emails from your inbox
- 📎 **Attachments** — Support for multiple file attachments
- 📅 **Scheduled Emails** — Schedule emails to be sent at specific times
- 📝 **Email Templates** — Use Jinja2 templates for dynamic email content
- 🔁 **Auto-Reply** — Set up automatic replies based on rules
- 📊 **Logging** — Full logging of all email activity
- 🔒 **Secure** — Uses environment variables for credentials, supports TLS/SSL

## Project Structure

```
mailbot/
├── main.py                 # Entry point
├── config.py               # Configuration & environment variables
├── mail_sender.py          # Email sending functionality
├── mail_reader.py          # Email reading/fetching functionality
├── mail_scheduler.py       # Scheduled email functionality
├── auto_reply.py           # Auto-reply engine
├── template_engine.py      # Email template rendering
├── utils.py                # Utility functions
├── templates/
│   ├── welcome.html        # Welcome email template
│   └── notification.html   # Notification email template
├── logs/
│   └── mailbot.log         # Log file (auto-generated)
├── requirements.txt        # Python dependencies
├── .env.example            # Example environment variables
├── .gitignore              # Git ignore rules
└── tests/
    ├── test_sender.py      # Tests for mail sender
    └── test_reader.py      # Tests for mail reader
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/pranees2004/goole.git
cd goole
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your email credentials
```

### 4. Run MailBot

```bash
python main.py
```

## Usage Examples

### Send a simple email
```python
from mail_sender import MailSender

sender = MailSender()
sender.send(
    to="recipient@example.com",
    subject="Hello from MailBot!",
    body="This is an automated email."
)
```

### Send an HTML email with attachment
```python
sender.send_html(
    to="recipient@example.com",
    subject="Monthly Report",
    template="notification",
    context={"name": "John", "message": "Your report is ready."},
    attachments=["report.pdf"]
)
```

### Read inbox emails
```python
from mail_reader import MailReader

reader = MailReader()
emails = reader.fetch_inbox(limit=10)
for email in emails:
    print(f"From: {email['from']} | Subject: {email['subject']}")
```

### Schedule an email
```python
from mail_scheduler import MailScheduler

scheduler = MailScheduler()
scheduler.schedule(
    to="recipient@example.com",
    subject="Reminder",
    body="Don't forget your meeting!",
    send_at="2026-04-16 09:00:00"
)
scheduler.start()
```

## Configuration

All configuration is managed via environment variables (`.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP server port | `587` |
| `IMAP_HOST` | IMAP server hostname | `imap.gmail.com` |
| `IMAP_PORT` | IMAP server port | `993` |
| `EMAIL_ADDRESS` | Your email address | — |
| `EMAIL_PASSWORD` | Your email/app password | — |
| `LOG_LEVEL` | Logging level | `INFO` |

## License

MIT License — see [LICENSE](LICENSE) for details.
