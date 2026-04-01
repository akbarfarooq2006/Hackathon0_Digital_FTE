---
name: gmail-sender
description: |
  Draft and send emails via Gmail API. Creates draft emails in Pending_Approval/ for human 
  review, then sends them after approval. Logs all sent emails to Briefings/ for audit trail.
  Use this skill when you need to reply to emails, send new messages, or manage email 
  communications. Triggers when user mentions sending email, replying to email, drafting 
  email, or any email composition task.
---

# Gmail Sender Skill

Draft and send emails via Gmail API with human-in-the-loop approval.

## Prerequisites

### 1. Gmail API Setup (Same as gmail-watcher)

This skill shares credentials with **gmail-watcher**. If you've already set up Gmail monitoring, you're ready to go!

```bash
# Install dependencies
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib

# Authenticate (if not already done)
cd .qwen/skills/gmail-watcher
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

### 2. Required Scopes

For sending emails, you need these Gmail API scopes:

```python
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',   # Read emails
    'https://www.googleapis.com/auth/gmail.send',       # Send emails
    'https://www.googleapis.com/auth/gmail.compose'     # Create drafts
]
```

If you authenticated with only readonly scope, re-authenticate:

```bash
# Delete old token to force re-authentication
rm token.json
python scripts/gmail_watcher.py ../../../AI_Employee_Vault --authenticate
```

## Configuration

### Environment Variables (.env)

```bash
# Gmail API credentials
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
VAULT_PATH=./AI_Employee_Vault

# Default sender (optional, auto-detected from Gmail)
DEFAULT_FROM=your.email@example.com
```

## Usage

### Draft an Email (Creates in Pending_Approval/)

```bash
claude "Draft an email to client@example.com about the invoice status"
```

This creates a file in `Pending_Approval/` like:

```markdown
---
type: email_draft
to: client@example.com
subject: Invoice Status Update
created: 2026-03-30T10:30:00Z
status: pending_approval
---

# Email Draft

## To
client@example.com

## Subject
Invoice Status Update

## Body

Dear Client,

I hope this email finds you well. I'm writing to update you on the invoice status...

Best regards,
[Your Name]

---
## Instructions
- Move to /Approved to send this email
- Move to /Rejected to discard
```

### Send Approved Emails

```bash
# Send all approved emails
cd .qwen/skills/gmail-sender
python scripts/send_email.py ../../../AI_Employee_Vault --action send

# Send a specific email
python scripts/send_email.py ../../../AI_Employee_Vault --action send --file EMAIL_20260330_invoice.md
```

### List Drafts and Approved

```bash
# List all pending and approved emails
python scripts/send_email.py ../../../AI_Employee_Vault --action list
```

### Reply to an Email

```bash
claude "Reply to the email from John about the project deadline"
```

This will:
1. Read the original email from `Needs_Action/`
2. Create a reply draft in `Pending_Approval/`
3. Wait for approval before sending

## Workflow

```
User requests email
       ↓
Claude drafts email content
       ↓
Save to Pending_Approval/
       ↓
Human reviews & edits (optional)
       ↓
Move to Approved/
       ↓
Run send_email.py --action send
       ↓
Email sent via Gmail API
       ↓
Log to Briefings/
       ↓
Move to Done/
```

## Email Draft Format

```markdown
---
type: email_draft
to: recipient@example.com
cc: cc@example.com (optional)
bcc: bcc@example.com (optional)
subject: Email Subject Line
created: 2026-03-30T10:30:00Z
in_reply_to: original_email_id (optional, for replies)
status: pending_approval
---

# Email Draft

## To
recipient@example.com

## Subject
Email Subject Line

## Body

Dear Recipient,

Email content goes here. You can use:

- Bullet points
- **Bold text**
- Numbered lists

Best regards,
Sender Name

---
## Instructions
- Review and edit content above
- Move to /Approved to send
- Move to /Rejected to discard
```

## Scripts

| Script | Purpose |
|--------|---------|
| `send_email.py` | Main script to send approved emails |
| `draft_email.py` | Create email drafts programmatically |

### send_email.py Usage

```bash
# Send all approved emails
python scripts/send_email.py <vault_path> --action send

# List pending and approved
python scripts/send_email.py <vault_path> --action list

# Preview an email without sending
python scripts/send_email.py <vault_path> --action preview --file FILENAME.md

# Dry run (validate but don't send)
python scripts/send_email.py <vault_path> --action send --dry-run
```

## Integration

Works with:
- **gmail-watcher**: Read incoming emails, reply to them
- **approval-workflow**: Human review before sending
- **vault-processor**: Move files between folders

## Email Templates

### Reply Template

```markdown
## Body

Dear {sender_name},

Thank you for your email regarding {topic}.

{response_content}

Please let me know if you have any questions.

Best regards,
{your_name}
```

### New Message Template

```markdown
## Body

Dear {recipient_name},

I hope this email finds you well.

{main_content}

Looking forward to hearing from you.

Best regards,
{your_name}
```

### Follow-up Template

```markdown
## Body

Dear {recipient_name},

I'm following up on my previous email about {topic}.

{follow_up_content}

Please let me know your thoughts.

Best regards,
{your_name}
```

## Security Notes

- `token.json` contains OAuth tokens - never commit to git
- `credentials.json` has client secrets - keep private
- All emails require human approval before sending
- Sent emails are logged for audit trail

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run authentication with correct scopes |
| Email not sending | Check Gmail API is enabled |
| Token expired | Delete `token.json`, re-authenticate |
| Permission denied | Ensure gmail.send scope is granted |

## Best Practices

1. **Always draft first** - Never send without approval
2. **Review carefully** - Check recipient, subject, and content
3. **Keep records** - All sent emails are logged
4. **Use templates** - Consistent formatting
5. **Respond promptly** - Aim for <24 hour response time

## Example: Full Email Workflow

### Step 1: Receive Email

```
Gmail Watcher detects new email
       ↓
Creates: Needs_Action/EMAIL_20260330_client_request.md
```

### Step 2: Draft Reply

```bash
claude "Draft a reply to the client's invoice request"
```

Creates: `Pending_Approval/EMAIL_REPLY_20260330_client.md`

### Step 3: Human Review

- Review content in `Pending_Approval/`
- Edit if needed
- Move to `Approved/` when ready

### Step 4: Send Email

```bash
cd .qwen/skills/gmail-sender
python scripts/send_email.py ../../../AI_Employee_Vault --action send
```

### Step 5: Confirmation

```
Email sent successfully!
Logged to: Briefings/email_sent_20260330_103000.md
Moved to: Done/EMAIL_REPLY_20260330_client.md
```
