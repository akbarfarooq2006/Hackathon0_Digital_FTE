#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email Draft Creator - Create email draft files.

This script helps create email draft files in Pending_Approval/ folder.

Usage:
    python draft_email.py <vault_path> --to EMAIL --subject SUBJECT --body BODY
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime


def create_draft(vault_path: Path, to: str, subject: str, body: str, 
                 cc: str = None, in_reply_to: str = None) -> Path:
    """
    Create an email draft file.
    
    Args:
        vault_path: Path to vault
        to: Recipient email
        subject: Email subject
        body: Email body
        cc: CC recipients (optional)
        in_reply_to: Message ID for replies (optional)
    
    Returns:
        Path: Path to created file
    """
    pending_approval = vault_path / 'Pending_Approval'
    pending_approval.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_subject = subject.replace(' ', '_').replace('/', '_')[:30]
    filename = f'EMAIL_{timestamp}_{safe_subject}.md'
    filepath = pending_approval / filename
    
    cc_line = f'\ncc: {cc}' if cc else ''
    reply_line = f'\nin_reply_to: {in_reply_to}' if in_reply_to else ''
    
    content = f'''---
type: email_draft
to: {to}{cc_line}
subject: {subject}{reply_line}
created: {datetime.now().isoformat()}
status: pending_approval
---

# Email Draft

## To
{to}

## Subject
{subject}

## Body

{body}

---
## Instructions
1. Review and edit the content above
2. Move this file to /Approved to send
3. Move to /Rejected to discard
'''
    
    filepath.write_text(content, encoding='utf-8')
    return filepath


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Email Draft Creator')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--to', type=str, required=True, help='Recipient email')
    parser.add_argument('--subject', type=str, required=True, help='Email subject')
    parser.add_argument('--body', type=str, required=True, help='Email body')
    parser.add_argument('--cc', type=str, help='CC recipients')
    parser.add_argument('--reply-to', type=str, help='Message ID to reply to')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    
    # Create draft
    filepath = create_draft(
        vault_path=vault_path,
        to=args.to,
        subject=args.subject,
        body=args.body,
        cc=args.cc,
        in_reply_to=args.reply_to
    )
    
    print(f"Draft created: {filepath}")
    print("\nNext steps:")
    print("1. Review/edit the draft file")
    print("2. Move to /Approved when ready")
    print("3. Run: python send_email.py <vault> --action send")


if __name__ == "__main__":
    main()
