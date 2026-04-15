"""
MailBot - Main Entry Point
A powerful automated email bot for sending, reading, and scheduling emails.
"""

import sys
import argparse
from config import Config
from mail_sender import MailSender
from mail_reader import MailReader
from mail_scheduler import MailScheduler
from auto_reply import AutoReply
from utils import setup_logger


logger = setup_logger("mailbot")


def cmd_send(args):
    """Send an email from command line."""
    sender = MailSender()
    attachments = args.attachments.split(",") if args.attachments else None

    if args.html:
        sender.send_html(
            to=args.to,
            subject=args.subject,
            html_body=args.body,
            attachments=attachments,
        )
    else:
        sender.send(
            to=args.to,
            subject=args.subject,
            body=args.body,
            attachments=attachments,
        )
    print(f"✅ Email sent to {args.to}")


def cmd_read(args):
    """Read inbox emails from command line."""
    reader = MailReader()
    emails = reader.fetch_inbox(limit=args.limit, unread_only=args.unread)

    if not emails:
        print("📭 No emails found.")
        return

    for i, email_data in enumerate(emails, 1):
        print(f"\n{'='*60}")
        print(f"📧 Email {i}")
        print(f"  From:    {email_data['from']}")
        print(f"  Subject: {email_data['subject']}")
        print(f"  Date:    {email_data['date']}")
        if email_data['attachments']:
            print(f"  📎 Attachments: {', '.join(email_data['attachments'])}")
        if args.show_body:
            print(f"  Body:\n{email_data['body'][:500]}")
    print(f"\n{'='*60}")
    print(f"📬 Total: {len(emails)} email(s)")


def cmd_search(args):
    """Search emails from command line."""
    reader = MailReader()
    emails = reader.search_emails(query=args.query, limit=args.limit)

    if not emails:
        print(f"🔍 No emails found matching '{args.query}'")
        return

    for i, email_data in enumerate(emails, 1):
        print(f"  {i}. [{email_data['date']}] {email_data['from']} — {email_data['subject']}")
    print(f"\n🔍 Found {len(emails)} email(s) matching '{args.query}'")


def cmd_schedule(args):
    """Schedule an email from command line."""
    scheduler = MailScheduler()
    scheduler.schedule(
        to=args.to,
        subject=args.subject,
        body=args.body,
        send_at=args.send_at,
    )
    print(f"⏰ Email scheduled for {args.send_at}")
    print("Starting scheduler... (Press Ctrl+C to stop)")

    scheduler.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        scheduler.stop()
        print("\n🛑 Scheduler stopped.")


def cmd_autoreply(args):
    """Start auto-reply from command line."""
    auto = AutoReply()

    if args.keyword:
        auto.add_keyword_rule(
            name=f"keyword-{args.keyword}",
            keyword=args.keyword,
            reply_body=args.reply_message or Config.AUTO_REPLY_MESSAGE,
        )

    if args.sender:
        auto.add_sender_rule(
            name=f"sender-{args.sender}",
            sender_email=args.sender,
            reply_body=args.reply_message or Config.AUTO_REPLY_MESSAGE,
        )

    if not auto.rules:
        auto.add_rule(
            name="default-reply-all",
            condition=lambda e: True,
            reply_body=args.reply_message or Config.AUTO_REPLY_MESSAGE,
        )

    print(f"🤖 Auto-reply started with {len(auto.rules)} rule(s)")
    print(f"   Checking every {args.interval} seconds...")
    print("   Press Ctrl+C to stop.\n")

    auto.start(check_interval=args.interval)
    try:
        while True:
            pass
    except KeyboardInterrupt:
        auto.stop()
        print("\n🛑 Auto-reply stopped.")


def cmd_interactive():
    """Run MailBot in interactive mode."""
    print("\n" + "="*50)
    print("  📧 MailBot — Interactive Mode")
    print("="*50)
    print("\nCommands:")
    print("  1. Send an email")
    print("  2. Read inbox")
    print("  3. Search emails")
    print("  4. Schedule an email")
    print("  5. Start auto-reply")
    print("  6. Exit")
    print()

    while True:
        choice = input("Choose an option (1-6): ").strip()

        if choice == "1":
            to = input("  To: ").strip()
            subject = input("  Subject: ").strip()
            body = input("  Body: ").strip()
            sender = MailSender()
            sender.send(to=to, subject=subject, body=body)
            print("  ✅ Email sent!\n")

        elif choice == "2":
            limit = int(input("  How many emails? (default 5): ").strip() or "5")
            reader = MailReader()
            emails = reader.fetch_inbox(limit=limit)
            for i, e in enumerate(emails, 1):
                print(f"  {i}. {e['from']} — {e['subject']}")
            print()

        elif choice == "3":
            query = input("  Search query: ").strip()
            reader = MailReader()
            emails = reader.search_emails(query=query)
            for i, e in enumerate(emails, 1):
                print(f"  {i}. {e['from']} — {e['subject']}")
            print()

        elif choice == "4":
            to = input("  To: ").strip()
            subject = input("  Subject: ").strip()
            body = input("  Body: ").strip()
            send_at = input("  Send at (YYYY-MM-DD HH:MM:SS): ").strip()
            scheduler = MailScheduler()
            scheduler.schedule(to=to, subject=subject, body=body, send_at=send_at)
            print(f"  ⏰ Scheduled for {send_at}\n")

        elif choice == "5":
            message = input("  Reply message: ").strip()
            auto = AutoReply()
            auto.add_rule("default", lambda e: True, reply_body=message)
            auto.start()
            print("  🤖 Auto-reply started. Press Enter to stop.")
            input()
            auto.stop()
            print("  🛑 Auto-reply stopped.\n")

        elif choice == "6":
            print("  👋 Goodbye!")
            break

        else:
            print("  ❌ Invalid option. Try again.\n")


def main():
    parser = argparse.ArgumentParser(
        description="📧 MailBot — Automated Email Bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    # Send command
    send_parser = subparsers.add_parser("send", help="Send an email")
    send_parser.add_argument("--to", required=True, help="Recipient email")
    send_parser.add_argument("--subject", required=True, help="Email subject")
    send_parser.add_argument("--body", required=True, help="Email body")
    send_parser.add_argument("--html", action="store_true", help="Send as HTML")
    send_parser.add_argument("--attachments", help="Comma-separated file paths")

    # Read command
    read_parser = subparsers.add_parser("read", help="Read inbox emails")
    read_parser.add_argument("--limit", type=int, default=5, help="Number of emails")
    read_parser.add_argument("--unread", action="store_true", help="Only unread emails")
    read_parser.add_argument("--show-body", action="store_true", help="Show email body")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search emails")
    search_parser.add_argument("--query", required=True, help="Search query")
    search_parser.add_argument("--limit", type=int, default=20, help="Max results")

    # Schedule command
    sched_parser = subparsers.add_parser("schedule", help="Schedule an email")
    sched_parser.add_argument("--to", required=True, help="Recipient email")
    sched_parser.add_argument("--subject", required=True, help="Email subject")
    sched_parser.add_argument("--body", required=True, help="Email body")
    sched_parser.add_argument("--send-at", required=True, help="Send time (YYYY-MM-DD HH:MM:SS)")

    # Auto-reply command
    auto_parser = subparsers.add_parser("autoreply", help="Start auto-reply")
    auto_parser.add_argument("--keyword", help="Trigger keyword")
    auto_parser.add_argument("--sender", help="Trigger sender email")
    auto_parser.add_argument("--reply-message", help="Reply message")
    auto_parser.add_argument("--interval", type=int, default=60, help="Check interval (seconds)")

    args = parser.parse_args()

    # Validate config
    try:
        Config.validate()
    except ValueError as e:
        print(f"⚠️  Configuration Error:\n{e}")
        print("\nPlease set up your .env file. See .env.example for reference.")
        sys.exit(1)

    if args.command == "send":
        cmd_send(args)
    elif args.command == "read":
        cmd_read(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "autoreply":
        cmd_autoreply(args)
    else:
        cmd_interactive()


if __name__ == "__main__":
    main()
