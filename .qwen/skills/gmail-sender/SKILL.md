---
name: gmail-sender
description: |
  Draft and send emails via Gmail API with human-in-the-loop approval. 
  Provides MCP server tools: email_send(), email_draft(), email_list().
  Use this skill when user mentions sending email, replying to email, drafting 
  email, listing emails, or any email composition task. Always use email_draft 
  for outgoing emails - never send directly without approval.
---

# Gmail Sender Skill (MCP Server)

Draft and send emails via Gmail MCP server with human-in-the-loop approval.

## Prerequisites

### 1. Gmail API Setup

Your `secrets/credential.json` is already configured. Just need to authenticate:

```bash
cd .qwen/skills/gmail-watcher/scripts
python authenticate.py
```

**Expected output:**
```
✓ Authenticated as: your.email@gmail.com
✓ Token saved to: data/gmail_token.json
```

### 2. Install Dependencies

```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

## Starting the MCP Server

```bash
cd .qwen/skills/gmail-sender/scripts
python email_mcp_server.py
```

The server runs on stdin/stdout using MCP protocol. It will be automatically detected by Qwen Code.

## Available MCP Tools

| Tool | Purpose | Usage |
|------|---------|-------|
| `email_list` | List recent emails | List unread emails |
| `email_draft` | Create draft for review | Save to Pending_Approval/ |
| `email_send` | Send email immediately | Only for pre-approved emails |

### email_list

List recent emails from Gmail inbox.

**Parameters:**
- `max_results` (optional): Max emails to return (default: 10)
- `query` (optional): Gmail search query (default: is:unread)

**Example:**
```
Call tool: email_list(max_results=5, query="is:unread")
```

### email_draft (RECOMMENDED)

Create an email draft in `Pending_Approval/` for human review.

**ALWAYS use this for outgoing emails - never send directly.**

**Parameters:**
- `to` (required): Recipient email
- `subject` (required): Email subject
- `body` (required): Email body text
- `cc` (optional): CC recipients
- `reply_to` (optional): Message ID to reply to

**Example:**
```
Call tool: email_draft(
  to="client@example.com",
  subject="Re: Project Update",
  body="Thank you for your email..."
)
```

**Creates file in:**
```
AI_Employee_Vault/Pending_Approval/
└── EMAIL_REPLY_20260408_103000_Project_Update.md
```

### email_send

Send an email immediately via Gmail API.

**⚠️ WARNING: Only use for pre-approved emails. For normal workflow, use email_draft.**

**Parameters:**
- `to` (required): Recipient email
- `subject` (required): Email subject
- `body` (required): Email body text
- `cc` (optional): CC recipients

**Example:**
```
Call tool: email_send(
  to="client@example.com",
  subject="Invoice #1234",
  body="Please find attached..."
)
```

## Workflow: Email Reply

```
1. Email arrives in Needs_Action/
   Gmail Watcher detects new email
         ↓
2. Qwen reads email
   qwen "Process Needs_Action folder"
         ↓
3. Qwen drafts reply via MCP
   email_draft(to, subject, body)
         ↓
4. Draft saved to Pending_Approval/
   qwen reviews content
         ↓
5. Human moves draft to Approved/
   (or Rejected/ to discard)
         ↓
6. Email sent via email_send or send_email.py
   Logged to Briefings/
   Moved to Done/
```

## Configuration

### Credentials

| File | Location | Purpose |
|------|----------|---------|
| `credential.json` | `secrets/credential.json` | Google OAuth credentials |
| `gmail_token.json` | `data/gmail_token.json` | OAuth token (auto-generated) |

### Environment Variables (.env)

```bash
GMAIL_CREDENTIALS_PATH=./secrets/credential.json
GMAIL_TOKEN_PATH=./data/gmail_token.json
VAULT_PATH=./AI_Employee_Vault
```

## Scripts

| Script | Purpose |
|--------|---------|
| `email_mcp_server.py` | MCP server (run continuously) |
| `send_email.py` | CLI tool to send approved emails |

### send_email.py Usage

```bash
# Send all approved emails
python send_email.py <vault_path> --action send

# List pending/approved emails
python send_email.py <vault_path> --action list

# Preview before sending
python send_email.py <vault_path> --action preview --file FILENAME.md
```

## Security Notes

- `data/gmail_token.json` contains OAuth tokens - never commit to git
- `secrets/credential.json` has client secrets - keep private
- All emails require human approval before sending
- Sent emails are logged for audit trail

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run `python authenticate.py` |
| Token expired | Delete `data/gmail_token.json`, re-authenticate |
| MCP server not responding | Check server is running |
| Email not sending | Verify file is in `Approved/` folder |
| Gmail API quota exceeded | Check Google Cloud Console quotas |

## Integration

Works with:
- **gmail-watcher**: Detects incoming emails
- **vault-processor**: Processes email action files
- **approval-workflow**: Human approval workflow

## Best Practices

1. **Always use email_draft** - Never send without approval
2. **Review drafts** - Check content before approving
3. **Log all actions** - Sent emails logged automatically
4. **Rotate tokens** - Re-authenticate every 90 days
5. **Monitor API usage** - Check Gmail API quota
