#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Sender - Send emails via Gmail API.

This script reads approved email drafts from the Approved/ folder,
sends them via Gmail API, and logs the results to Briefings/.

Usage:
    python send_email.py <vault_path> --action <send|list|preview> [--file FILENAME]
"""

import sys
import os
import logging
import argparse
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Add Gmail dependencies
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# Gmail API scopes - need send permission
SCOPES = [
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.readonly'
]


class GmailSender:
    """
    Send emails via Gmail API with approval workflow integration.
    """
    
    def __init__(self, vault_path: str, credentials_path: str = None, token_path: str = None):
        """
        Initialize Gmail Sender.
        
        Args:
            vault_path: Path to Obsidian vault root
            credentials_path: Path to Gmail OAuth credentials JSON
            token_path: Path to OAuth token file
        """
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.briefings = self.vault_path / 'Briefings'
        self.rejected = self.vault_path / 'Rejected'
        
        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.done, self.briefings, self.rejected]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Set credential paths
        self.credentials_path = Path(credentials_path) if credentials_path else self.vault_path.parent / 'credentials.json'
        self.token_path = Path(token_path) if token_path else self.vault_path.parent / 'token.json'
        
        self.service = None
        self.logger = logging.getLogger('GmailSender')
        self.user_email = None
    
    def authenticate(self):
        """
        Authenticate with Gmail API.
        
        Returns:
            bool: True if authentication successful
        """
        creds = None
        
        # Load from token file
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
                self.logger.info("Loaded existing credentials")
            except Exception as e:
                self.logger.warning(f"Failed to load token: {e}")
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                self._save_token(creds)
                self.logger.info("Refreshed expired token")
            except Exception as e:
                self.logger.warning(f"Failed to refresh token: {e}")
                creds = None
        
        # Need to authenticate
        if not creds or not creds.valid:
            self.logger.warning("No valid credentials found")
            self.logger.info("Please run authentication via gmail-watcher first:")
            self.logger.info("  cd .qwen/skills/gmail-watcher")
            self.logger.info("  python scripts/gmail_watcher.py <vault> --authenticate")
            return False
        
        # Build Gmail service
        try:
            self.service = build('gmail', 'v1', credentials=creds)
            
            # Get user email
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')
            
            self.logger.info(f"Authenticated as: {self.user_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to build Gmail service: {e}")
            return False
    
    def _save_token(self, creds):
        """Save OAuth token to file."""
        try:
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        except Exception as e:
            self.logger.error(f"Failed to save token: {e}")
    
    def list_emails(self):
        """
        List pending and approved email drafts.
        
        Returns:
            dict: Lists of pending and approved emails
        """
        pending = list(self.pending_approval.glob('EMAIL_*.md'))
        approved = list(self.approved.glob('EMAIL_*.md'))
        
        return {
            'pending': pending,
            'approved': approved,
            'pending_count': len(pending),
            'approved_count': len(approved)
        }
    
    def parse_email_file(self, filepath: Path) -> dict:
        """
        Parse email draft from markdown file.
        
        Args:
            filepath: Path to email draft file
            
        Returns:
            dict: Email data (to, subject, body, etc.)
        """
        content = filepath.read_text(encoding='utf-8')
        
        email_data = {
            'to': None,
            'cc': None,
            'bcc': None,
            'subject': None,
            'body': None,
            'in_reply_to': None,
            'raw_content': content
        }
        
        # Parse frontmatter
        if '---' in content:
            parts = content.split('---', 2)
            if len(parts) >= 2:
                frontmatter = parts[1].strip()
                for line in frontmatter.split('\n'):
                    if ':' in line:
                        key, value = line.split(':', 1)
                        key = key.strip().lower()
                        value = value.strip()
                        
                        if key == 'to':
                            email_data['to'] = value
                        elif key == 'cc':
                            email_data['cc'] = value
                        elif key == 'bcc':
                            email_data['bcc'] = value
                        elif key == 'subject':
                            email_data['subject'] = value
                        elif key == 'in_reply_to':
                            email_data['in_reply_to'] = value
        
        # Parse body from markdown content
        body_parts = content.split('## Body', 1)
        if len(body_parts) > 1:
            # Get content after ## Body, stop at next section or instructions
            body_content = body_parts[1].strip()
            
            # Remove instructions section if present
            if '---' in body_content:
                body_content = body_content.split('---')[0].strip()
            elif '## Instructions' in body_content:
                body_content = body_content.split('## Instructions')[0].strip()
            
            email_data['body'] = body_content
        else:
            # Fallback: get everything after frontmatter
            if len(parts) > 2:
                email_data['body'] = parts[2].strip()
        
        # Parse To from ## To section if not in frontmatter
        if not email_data['to']:
            to_match = content.split('## To', 1)
            if len(to_match) > 1:
                to_line = to_match[1].strip().split('\n')[0].strip()
                email_data['to'] = to_line
        
        # Parse Subject from ## Subject section if not in frontmatter
        if not email_data['subject']:
            subject_match = content.split('## Subject', 1)
            if len(subject_match) > 1:
                subject_line = subject_match[1].strip().split('\n')[0].strip()
                email_data['subject'] = subject_line
        
        return email_data
    
    def create_message(self, sender: str, to: str, subject: str, body: str, 
                       cc: str = None, in_reply_to: str = None) -> dict:
        """
        Create a Gmail API message.
        
        Args:
            sender: Sender email address
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (optional)
            in_reply_to: Message ID to reply to (optional)
            
        Returns:
            dict: Gmail API message object
        """
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = sender
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        
        if in_reply_to:
            message['In-Reply-To'] = in_reply_to
            message['References'] = in_reply_to
        
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    def send_email(self, filepath: Path, dry_run: bool = False) -> dict:
        """
        Send an approved email.
        
        Args:
            filepath: Path to approved email file
            dry_run: If True, validate but don't send
            
        Returns:
            dict: Result with status and details
        """
        result = {
            'success': False,
            'file': filepath.name,
            'message_id': None,
            'error': None
        }
        
        try:
            # Parse email file
            email_data = self.parse_email_file(filepath)
            
            # Validate required fields
            if not email_data['to']:
                result['error'] = 'Missing recipient (to)'
                return result
            
            if not email_data['subject']:
                result['error'] = 'Missing subject'
                return result
            
            if not email_data['body']:
                result['error'] = 'Missing body content'
                return result
            
            self.logger.info(f"Sending email to: {email_data['to']}")
            self.logger.info(f"Subject: {email_data['subject']}")
            
            if dry_run:
                self.logger.info("DRY RUN - Email validated but not sent")
                result['success'] = True
                result['message'] = 'Dry run successful'
                return result
            
            # Create message
            message = self.create_message(
                sender=self.user_email,
                to=email_data['to'],
                subject=email_data['subject'],
                body=email_data['body'],
                cc=email_data['cc'],
                in_reply_to=email_data['in_reply_to']
            )
            
            # Send via Gmail API
            sent_message = self.service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            result['success'] = True
            result['message_id'] = sent_message.get('id')
            result['thread_id'] = sent_message.get('threadId')
            
            self.logger.info(f"Email sent successfully! Message ID: {result['message_id']}")
            
            # Log to briefings
            self._log_sent_email(filepath, email_data, result)
            
            # Move to Done
            self._move_to_done(filepath)
            
            return result
            
        except HttpError as error:
            result['error'] = f'Gmail API error: {error}'
            self.logger.error(f"Failed to send email: {error}")
            return result
            
        except Exception as e:
            result['error'] = str(e)
            self.logger.error(f"Unexpected error: {e}")
            return result
    
    def send_all_approved(self, dry_run: bool = False) -> list:
        """
        Send all approved emails.
        
        Args:
            dry_run: If True, validate but don't send
            
        Returns:
            list: List of results for each email
        """
        approved_files = list(self.approved.glob('EMAIL_*.md'))
        
        if not approved_files:
            self.logger.info("No approved emails to send")
            return []
        
        self.logger.info(f"Found {len(approved_files)} approved emails")
        
        results = []
        for filepath in approved_files:
            result = self.send_email(filepath, dry_run)
            results.append(result)
        
        # Summary
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        
        self.logger.info(f"Send complete: {success_count} succeeded, {fail_count} failed")
        
        return results
    
    def _log_sent_email(self, filepath: Path, email_data: dict, result: dict):
        """Log sent email to Briefings folder."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_filename = f"email_sent_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        log_file = self.briefings / log_filename
        
        log_content = f'''---
type: email_sent_log
original_file: {filepath.name}
sent: {timestamp}
status: sent
message_id: {result.get('message_id', 'N/A')}
---

# Email Sent Log

## Sent
{timestamp}

## Email Details

**To:** {email_data['to']}
**Subject:** {email_data['subject']}
**CC:** {email_data.get('cc', 'N/A')}

## Content

{email_data['body']}

## Result
- Status: Successfully sent
- Message ID: {result.get('message_id', 'N/A')}
- Thread ID: {result.get('thread_id', 'N/A')}
'''
        
        log_file.write_text(log_content, encoding='utf-8')
        self.logger.info(f"Logged to: {log_file}")
    
    def _move_to_done(self, filepath: Path):
        """Move processed email to Done folder."""
        try:
            dest = self.done / filepath.name
            filepath.rename(dest)
            self.logger.info(f"Moved to Done: {dest.name}")
        except Exception as e:
            self.logger.warning(f"Failed to move file to Done: {e}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Gmail Sender for AI Employee')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--action', type=str, choices=['send', 'list', 'preview'],
                       default='list', help='Action to perform')
    parser.add_argument('--file', type=str, help='Specific email file to process')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Validate but don\'t actually send')
    parser.add_argument('--credentials', type=str, help='Path to credentials.json')
    parser.add_argument('--token', type=str, help='Path to token.json')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create sender
    sender = GmailSender(
        vault_path=args.vault_path,
        credentials_path=args.credentials,
        token_path=args.token
    )
    
    if args.action == 'list':
        # List emails
        emails = sender.list_emails()
        
        print(f"\n=== Email Status ===")
        print(f"\nPending Approval: {emails['pending_count']}")
        for f in emails['pending']:
            print(f"  - {f.name}")
        
        print(f"\nApproved (ready to send): {emails['approved_count']}")
        for f in emails['approved']:
            print(f"  - {f.name}")
    
    elif args.action == 'preview':
        # Preview an email
        if not args.file:
            print("Error: --file required for preview")
            sys.exit(1)
        
        filepath = sender.approved / args.file
        if not filepath.exists():
            print(f"File not found: {filepath}")
            sys.exit(1)
        
        email_data = sender.parse_email_file(filepath)
        
        print(f"\n=== Email Preview ===")
        print(f"To: {email_data['to']}")
        print(f"Subject: {email_data['subject']}")
        print(f"CC: {email_data.get('cc', 'N/A')}")
        print(f"\nBody:\n{email_data['body']}")
    
    elif args.action == 'send':
        # Send emails
        print("Authenticating with Gmail API...")
        
        if not sender.authenticate():
            print("\nAuthentication failed. Please run:")
            print("  cd .qwen/skills/gmail-watcher")
            print("  python scripts/gmail_watcher.py <vault> --authenticate")
            sys.exit(1)
        
        if args.file:
            # Send specific file
            filepath = sender.approved / args.file
            if not filepath.exists():
                print(f"File not found: {filepath}")
                sys.exit(1)
            
            print(f"Sending: {filepath.name}")
            result = sender.send_email(filepath, args.dry_run)
            
            print(f"\n=== Result ===")
            print(f"Status: {'✅ Success' if result['success'] else '❌ Failed'}")
            if result['message_id']:
                print(f"Message ID: {result['message_id']}")
            if result['error']:
                print(f"Error: {result['error']}")
        else:
            # Send all approved
            if args.dry_run:
                print("DRY RUN MODE - Will validate but not send")
            
            results = sender.send_all_approved(args.dry_run)
            
            if results:
                print(f"\n=== Send Summary ===")
                success = sum(1 for r in results if r['success'])
                failed = len(results) - success
                print(f"Total: {len(results)}")
                print(f"Success: {success}")
                print(f"Failed: {failed}")
                
                print(f"\nDetails:")
                for r in results:
                    icon = '✅' if r['success'] else '❌'
                    print(f"  {icon} {r['file']}")
                    if r.get('error'):
                        print(f"      Error: {r['error']}")
            else:
                print("No emails to send")


if __name__ == "__main__":
    main()
