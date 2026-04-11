#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher - Monitor Gmail for new emails and create action files.

This watcher uses the Gmail API to check for new unread/important emails
and creates Markdown action files in the Needs_Action folder.

Usage:
    python gmail_watcher.py <vault_path> [--authenticate] [--interval SECONDS]
"""

import sys
import os
import logging
import argparse
from pathlib import Path
from datetime import datetime
import base64
from email import message_from_bytes

# Add parent directory to path for base_watcher (now in same directory)
sys.path.insert(0, str(Path(__file__).parent))

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)

from base_watcher import BaseWatcher


# Gmail API scopes
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


class GmailWatcher(BaseWatcher):
    """
    Watcher for Gmail that monitors for new unread/important emails.
    """
    
    def __init__(self, vault_path: str, credentials_path: str, token_path: str, 
                 check_interval: int = 120, keywords: list = None):
        """
        Initialize the Gmail Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            credentials_path: Path to Gmail OAuth credentials JSON
            token_path: Path to store OAuth token
            check_interval: Seconds between checks (default: 120)
            keywords: List of keywords to flag as high priority
        """
        super().__init__(vault_path, check_interval)
        
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        self.keywords = keywords or ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency']
        self.service = None
        self.processed_ids = set()
        
        # Load previously processed IDs from cache
        self._load_processed_cache()
    
    def authenticate(self):
        """
        Perform OAuth authentication and save token.
        """
        if not self.credentials_path.exists():
            print(f"Error: Credentials file not found: {self.credentials_path}")
            print("Please download credentials.json from Google Cloud Console")
            return False
        
        try:
            flow_instance = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES
            )
            creds = flow_instance.run_local_server(port=8080)
            
            # Save token
            self.token_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
            
            print("Authentication successful! Token saved.")
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            return False
    
    def _load_credentials(self):
        """
        Load or refresh OAuth credentials.
        """
        creds = None
        
        # Load from token file
        if self.token_path.exists():
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(self.token_path, 'w') as token:
                token.write(creds.to_json())
        
        # Build service
        if creds and creds.valid:
            self.service = build('gmail', 'v1', credentials=creds)
            return True
        
        return False
    
    def _load_processed_cache(self):
        """Load previously processed email IDs from cache file."""
        cache_file = self.vault_path / '.gmail_cache.json'
        if cache_file.exists():
            try:
                import json
                with open(cache_file) as f:
                    data = json.load(f)
                    self.processed_ids = set(data.get('processed_ids', []))
            except:
                pass
    
    def _save_processed_cache(self):
        """Save processed email IDs to cache file."""
        cache_file = self.vault_path / '.gmail_cache.json'
        try:
            import json
            # Keep only last 1000 IDs to prevent unbounded growth
            ids_list = list(self.processed_ids)[-1000:]
            with open(cache_file, 'w') as f:
                json.dump({'processed_ids': ids_list}, f)
        except:
            pass
    
    def check_for_updates(self) -> list:
        """
        Check for new unread/important emails.
        
        Returns:
            List of new email messages to process
        """
        if not self.service:
            if not self._load_credentials():
                self.logger.error("Failed to load Gmail credentials")
                return []
        
        try:
            # Search for unread important emails
            results = self.service.users().messages().list(
                userId='me',
                q='is:unread',
                maxResults=10
            ).execute()
            
            messages = results.get('messages', [])
            new_messages = []
            
            for msg in messages:
                if msg['id'] not in self.processed_ids:
                    new_messages.append(msg)
            
            return new_messages
            
        except Exception as e:
            self.logger.error(f"Error checking Gmail: {e}")
            return []
    
    def create_action_file(self, message) -> Path:
        """
        Create a Markdown action file for an email.
        
        Args:
            message: Gmail message object
            
        Returns:
            Path to created file
        """
        # Get full message details
        msg = self.service.users().messages().get(
            userId='me', 
            id=message['id'],
            format='full'
        ).execute()
        
        # Extract headers
        headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
        
        from_addr = headers.get('From', 'Unknown')
        subject = headers.get('Subject', 'No Subject')
        date = headers.get('Date', '')
        
        # Extract body
        body = self._extract_body(msg['payload'])
        
        # Determine priority
        priority = self._determine_priority(subject, from_addr, body)
        
        # Mark as processed
        self.processed_ids.add(message['id'])
        self._save_processed_cache()
        
        # Create action file
        safe_subject = self.sanitize_filename(subject)[:50]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'EMAIL_{timestamp}_{safe_subject}.md'
        filepath = self.needs_action / filename
        
        content = f'''---
type: email
from: {from_addr}
subject: {subject}
received: {self.get_timestamp()}
priority: {priority}
status: pending
gmail_id: {message['id']}
---

# Email: {subject}

## Sender
{from_addr}

## Received
{date or self.get_timestamp()}

## Content

{body}

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Take appropriate action
- [ ] Archive after processing

## Notes
<!-- Add your notes here -->
'''
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created action file for email: {subject}')
        
        return filepath
    
    def _extract_body(self, payload) -> str:
        """Extract text body from email payload."""
        # Try to find text/plain part
        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain':
                    data = part['body'].get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        
        # Fallback to body
        if 'body' in payload:
            data = payload['body'].get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        
        return '[No text content]'
    
    def _determine_priority(self, subject: str, from_addr: str, body: str) -> str:
        """Determine email priority based on content."""
        text = f"{subject} {body}".lower()
        
        # Check for urgent keywords
        for keyword in self.keywords:
            if keyword.lower() in text:
                return 'high'
        
        # Check for business keywords
        business_keywords = ['invoice', 'payment', 'billing', 'contract', 'urgent']
        for kw in business_keywords:
            if kw in text:
                return 'high'
        
        return 'normal'
    
    def run(self):
        """
        Main run loop - continuously monitors Gmail.
        """
        self.logger.info(f'Starting Gmail Watcher')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        # Load credentials
        if not self._load_credentials():
            self.logger.error("Failed to load Gmail credentials. Run with --authenticate first.")
            return
        
        self.logger.info("Gmail credentials loaded successfully")
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing emails: {e}')
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info('Gmail Watcher stopped by user')


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Gmail Watcher for AI Employee')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--authenticate', action='store_true', 
                       help='Run authentication flow')
    parser.add_argument('--interval', type=int, default=120,
                       help='Check interval in seconds (default: 120)')
    parser.add_argument('--keywords', type=str, default='',
                       help='Comma-separated keywords for high priority')
    # Resolve project root (2 levels up from watchers/)
    _project_root = Path(__file__).parent.parent

    parser.add_argument('--credentials', type=str,
                       default=str(_project_root / 'secrets' / 'credential.json'),
                       help='Path to Gmail credentials JSON')
    parser.add_argument('--token', type=str,
                       default=str(_project_root / 'data' / 'gmail_token.json'),
                       help='Path to store OAuth token')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    
    # Create watcher
    watcher = GmailWatcher(
        vault_path=args.vault_path,
        credentials_path=args.credentials,
        token_path=args.token,
        check_interval=args.interval,
        keywords=keywords
    )
    
    if args.authenticate:
        print("Starting Gmail authentication...")
        print("A browser window will open for you to grant access.")
        watcher.authenticate()
    else:
        watcher.run()


if __name__ == "__main__":
    import time
    main()
