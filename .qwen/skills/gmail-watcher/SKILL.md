---
name: gmail-watcher
description: |
  Monitor Gmail for new unread/important emails and create action files. Uses Google Gmail API 
  to fetch emails and creates Markdown files in Needs_Action/ for Claude Code processing. 
  Use this skill when setting up email monitoring for the AI Employee Silver Tier.
  Triggers when user mentions Gmail monitoring, email watcher, checking emails, or setting up 
  email notifications for the vault.
---

# Gmail Watcher Skill

Monitor Gmail inbox and create actionable files for new emails.

## Prerequisites

### 1. Google Cloud Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials (Desktop app)
5. Download `credentials.json` to project root

### 2. Install Dependencies
```bash
pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

### 3. First-Time Authentication
```bash
python scripts/gmail_watcher.py ../AI_Employee_Vault --authenticate
```

## Configuration

### Environment Variables (.env)
```bash
GMAIL_CREDENTIALS_PATH=./credentials.json
GMAIL_TOKEN_PATH=./token.json
VAULT_PATH=./AI_Employee_Vault
CHECK_INTERVAL=120
```

## Usage

### Start Watcher
```bash
cd .qwen/skills/gmail-watcher
python scripts/gmail_watcher.py ../../AI_Employee_Vault
```

### Run with Custom Settings
```bash
python scripts/gmail_watcher.py ../../AI_Employee_Vault \
  --interval 60 \
  --keywords "urgent,invoice,payment,asap"
```

## Action File Format

Creates file in `Needs_Action/`:

```markdown
---
type: email
from: client@example.com
subject: Invoice Request
received: 2026-03-30T10:30:00
priority: high
status: pending
gmail_id: 18abc123def456
---

# Email: Invoice Request

## Sender
client@example.com

## Received
2026-03-30 10:30 AM

## Content
Hi, I need an invoice for the recent project...

## Suggested Actions
- [ ] Reply to sender
- [ ] Forward to relevant party
- [ ] Create invoice
- [ ] Archive after processing
```

## Priority Detection

| Condition | Priority |
|-----------|----------|
| Subject contains "urgent", "asap", "emergency" | High |
| From VIP contacts (configured) | High |
| Contains "invoice", "payment", "billing" | High |
| Unread important emails | Normal |

## Workflow

```
Gmail API (poll every 2 min)
       ↓
New unread/important email?
       ↓
Create action file in Needs_Action/
       ↓
Claude Code processes email
       ↓
Reply/Forward/Archive
       ↓
Mark as processed (avoid duplicates)
```

## Scripts

| Script | Purpose |
|--------|---------|
| `gmail_watcher.py` | Main watcher script |
| `authenticate.py` | OAuth authentication helper |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Authentication failed | Re-run `--authenticate` |
| No emails detected | Check Gmail API is enabled |
| Rate limit errors | Increase CHECK_INTERVAL |
| Token expired | Delete `token.json`, re-authenticate |

## Security Notes

- `token.json` contains OAuth tokens - never commit to git
- `credentials.json` has client secrets - keep private
- Store in `.env` or secure location
- Tokens are stored locally, not synced

## Integration

Works with:
- **vault-processor**: Process email action files
- **email-sender**: Send replies
- **approval-workflow**: Flag sensitive emails for approval
