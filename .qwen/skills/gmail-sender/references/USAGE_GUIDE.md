# Gmail Sender - Complete Usage Guide

## Overview

The **gmail-sender** skill enables your AI Employee to:
1. **Draft emails** and save them for human review
2. **Send emails** via Gmail API after approval
3. **Log all sent emails** for audit trail

## Quick Start

### Step 1: Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### Step 2: Authenticate (One-Time)

If you haven't set up Gmail authentication yet:

```bash
cd .qwen/skills/gmail-watcher
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

This will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request Gmail API permissions (read + send)
4. Save credentials to `token.json`

### Step 3: Verify Authentication

```bash
cd .qwen/skills/gmail-sender
python scripts/send_email.py ../../../AI_Employee_Vault --action list
```

You should see:
```
=== Email Status ===

Pending Approval: 0
Approved (ready to send): 0
```

---

## Workflow: Send an Email

### Method 1: Via Qwen (Recommended)

```bash
qwen "Draft an email to client@example.com thanking them for their business"
```

This creates a draft in `Pending_Approval/`:

```markdown
---
type: email_draft
to: client@example.com
subject: Thank You
created: 2026-03-30T10:30:00Z
status: pending_approval
---

# Email Draft

## To
client@example.com

## Subject
Thank You

## Body

Dear Valued Client,

Thank you for your continued business...

Best regards,
[Your Name]

---
## Instructions
- Move to /Approved to send
- Move to /Rejected to discard
```

### Method 2: Manual Draft

```bash
cd .qwen/skills/gmail-sender
python scripts/draft_email.py ../../../AI_Employee_Vault \
  --to "client@example.com" \
  --subject "Project Update" \
  --body "Hi, Here's the project update you requested..."
```

---

## Review and Approve

1. Open the draft file in `Pending_Approval/`
2. Review and edit the content
3. **To Send:** Move file to `Approved/` folder
4. **To Discard:** Move file to `Rejected/` folder

---

## Send Approved Emails

### Send All Approved

```bash
cd .qwen/skills/gmail-sender
python scripts/send_email.py ../../../AI_Employee_Vault --action send
```

### Send Specific Email

```bash
python scripts/send_email.py ../../../AI_Employee_Vault \
  --action send \
  --file EMAIL_20260330_thank_you.md
```

### Dry Run (Test Without Sending)

```bash
python scripts/send_email.py ../../../AI_Employee_Vault \
  --action send \
  --dry-run
```

### Preview Email Before Sending

```bash
python scripts/send_email.py ../../../AI_Employee_Vault \
  --action preview \
  --file EMAIL_20260330_thank_you.md
```

---

## Email File Format

```markdown
---
type: email_draft
to: recipient@example.com
cc: manager@example.com        (optional)
bcc: secret@example.com        (optional)
subject: Email Subject
in_reply_to: <message-id>      (optional, for replies)
created: 2026-03-30T10:30:00Z
status: pending_approval
---

# Email Draft

## To
recipient@example.com

## Subject
Email Subject

## Body

Dear Recipient,

Email content goes here.

Best regards,
Sender

---
## Instructions
- Move to /Approved to send
- Move to /Rejected to discard
```

---

## Reply to Incoming Emails

### Step 1: Receive Email

Gmail Watcher creates file in `Needs_Action/`:
```
Needs_Action/EMAIL_20260330_client_request.md
```

### Step 2: Draft Reply

```bash
qwen "Reply to John's email about the project deadline"
```

This creates a reply draft in `Pending_Approval/` with:
- Original recipient auto-filled
- Subject prefixed with "Re:"
- `in_reply_to` field set for threading

### Step 3: Review and Send

1. Review draft in `Pending_Approval/`
2. Move to `Approved/` when ready
3. Run send command

---

## Logging and Audit Trail

### Sent Emails Log

All sent emails are logged to `Briefings/`:

```
Briefings/
└── email_sent_20260330_103000.md
```

Log file contains:
- Timestamp
- Recipient
- Subject
- Full email content
- Gmail Message ID
- Thread ID

### Completed Emails

After sending, original draft is moved to `Done/`:
```
Done/EMAIL_20260330_thank_you.md
```

---

## Command Reference

### List Emails

```bash
python scripts/send_email.py <vault> --action list
```

Shows:
- Pending drafts in `Pending_Approval/`
- Approved emails ready to send

### Preview Email

```bash
python scripts/send_email.py <vault> --action preview --file FILENAME.md
```

Shows:
- To, CC, Subject
- Full body content

### Send Emails

```bash
python scripts/send_email.py <vault> --action send [--dry-run] [--file FILENAME.md]
```

Options:
- `--dry-run`: Validate without sending
- `--file`: Send specific file only

### Create Draft

```bash
python scripts/draft_email.py <vault> \
  --to "email@example.com" \
  --subject "Subject" \
  --body "Email body text" \
  [--cc "cc@example.com"] \
  [--reply-to "message-id"]
```

---

## Troubleshooting

### Authentication Failed

**Error:** "No valid credentials found"

**Solution:**
```bash
cd .qwen/skills/gmail-watcher
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

### Missing Permissions

**Error:** "Insufficient permission"

**Solution:** Delete token and re-authenticate:
```bash
rm ../../token.json
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

### Email Not Sending

**Check:**
1. File is in `Approved/` folder (not `Pending_Approval/`)
2. File has `to:` and `subject:` fields
3. File has body content

### Token Expired

**Solution:** Refresh token automatically or re-authenticate:
```bash
rm ../../token.json
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

---

## Security Best Practices

1. **Never commit credentials**
   - Add to `.gitignore`:
     ```
     token.json
     credentials.json
     ```

2. **Always review before sending**
   - Human must move file to `Approved/`
   - Review content carefully

3. **Audit trail**
   - All sent emails logged to `Briefings/`
   - Original drafts moved to `Done/`

4. **Use approval workflow**
   - Never send without approval
   - Double-check recipients

---

## Integration Examples

### With gmail-watcher

```
Gmail Watcher → Detects new email
     ↓
Creates: Needs_Action/EMAIL_*.md
     ↓
Qwen reads and drafts reply
     ↓
Creates: Pending_Approval/EMAIL_REPLY_*.md
     ↓
Human approves (moves to Approved/)
     ↓
Gmail Sender → Sends email
     ↓
Logs to: Briefings/email_sent_*.md
```

### With approval-workflow

For sensitive emails (payments, legal, etc.):

```
Qwen detects sensitive topic
     ↓
Creates approval request in Pending_Approval/
     ↓
Human reviews and approves
     ↓
Gmail Sender sends after approval
```

---

## Example: Full Email Conversation

### Incoming Email

```
From: john@example.com
Subject: Project Timeline

Hi, when will the project be complete?
```

### Draft Reply

```bash
qwen "Reply to John's email about the project timeline"
```

### Review Draft

File created: `Pending_Approval/EMAIL_REPLY_project_timeline.md`

```markdown
---
to: john@example.com
subject: Re: Project Timeline
in_reply_to: <original-message-id>
---

## Body

Hi John,

Thanks for reaching out. The project is on track...

Best regards,
[Your Name]
```

### Approve and Send

```bash
# Move file to Approved/ (in Obsidian or file explorer)

# Then send
python scripts/send_email.py ../../../AI_Employee_Vault --action send
```

### Result

```
✅ Email sent successfully!
Message ID: 18abc123def456
Logged to: Briefings/email_sent_20260330_103000.md
Moved to: Done/EMAIL_REPLY_project_timeline.md
```

---

## API Reference

### GmailSender Class

```python
from send_email import GmailSender

sender = GmailSender(vault_path="./AI_Employee_Vault")

# Authenticate
if sender.authenticate():
    # Send all approved
    results = sender.send_all_approved()
    
    # Send specific file
    result = sender.send_email(filepath, dry_run=False)
    
    # List emails
    emails = sender.list_emails()
```

### parse_email_file()

```python
email_data = sender.parse_email_file(filepath)
# Returns: {to, cc, bcc, subject, body, in_reply_to, raw_content}
```

### create_message()

```python
message = sender.create_message(
    sender="me@example.com",
    to="recipient@example.com",
    subject="Hello",
    body="Email content",
    cc="manager@example.com"
)
```

---

## Support

For issues or questions:
1. Check logs in `Briefings/`
2. Review error messages
3. Verify authentication status
4. Check Gmail API quota limits
