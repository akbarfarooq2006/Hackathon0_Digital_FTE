# Gmail Watcher - Setup Guide

## Quick Start (3 Steps)

### Step 1: Install Dependencies

```bash
cd E:\IT learning file\Projects\Agentic_project\AI_Employee\Hackathon0_Digital_FTE
pip install -r requirements.txt
```

### Step 2: Authenticate with Gmail

Your `credentials.json` is already in the project root. Run:

```bash
cd .qwen/skills/gmail-watcher/scripts
python authenticate.py
```

This will:
1. Open a browser window
2. Ask you to sign in to Google
3. Request Gmail API permissions (read, send, compose)
4. Save `token.json` for future use

**Important:** Keep `token.json` private - it contains your OAuth credentials!

### Step 3: Start the Watcher

```bash
python gmail_watcher.py ../../../AI_Employee_Vault
```

The watcher will:
- Check Gmail every 2 minutes
- Create action files for new/important emails
- Save to `Needs_Action/` folder

---

## Configuration

### Environment Variables (Optional)

Create `.env` in project root:

```bash
# Gmail Watcher Configuration
GMAIL_CREDENTIALS_PATH=./credential.json
GMAIL_TOKEN_PATH=./token.json
VAULT_PATH=./AI_Employee_Vault
CHECK_INTERVAL=120
KEYWORDS=urgent,asap,invoice,payment,help,emergency
```

### Custom Settings

```bash
# Check every 60 seconds instead of 120
python gmail_watcher.py ../../../AI_Employee_Vault --interval 60

# Custom keywords for priority detection
python gmail_watcher.py ../../../AI_Employee_Vault --keywords "urgent,asap,billing"
```

---

## How It Works

```
┌─────────────────┐
│   Gmail API     │
│  (poll 2 min)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Check unread/  │
│  important      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Create .md     │
│  action file    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Needs_Action/  │
│  (Qwen reads)   │
└─────────────────┘
```

---

## Action File Format

When an email is detected, creates:

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

---

## Priority Detection

| Condition | Priority |
|-----------|----------|
| Subject contains "urgent", "asap", "emergency" | High |
| Contains "invoice", "payment", "billing" | High |
| From VIP contacts (configured) | High |
| Unread important emails | Normal |

---

## Integration with gmail-sender

After processing an email, you can reply using the gmail-sender skill:

```bash
# Qwen will draft a reply
qwen "Draft a reply to the email from John about the project"

# Creates draft in Pending_Approval/
# Move to Approved/ when ready
# Then send:
python ../gmail-sender/scripts/send_email.py ../../../AI_Employee_Vault --action send
```

---

## Troubleshooting

### "No valid credentials found"

**Solution:** Re-run authentication
```bash
python authenticate.py
```

### "Token expired"

**Solution:** Delete old token and re-authenticate
```bash
rm token.json
python authenticate.py
```

### "Gmail API not enabled"

**Solution:** Enable Gmail API in Google Cloud Console
1. Go to https://console.cloud.google.com/
2. Select your project
3. APIs & Services > Library
4. Search "Gmail API" and enable

### "No emails detected"

**Possible causes:**
- No unread emails
- Gmail API quota limit reached
- Incorrect OAuth scopes

**Solution:** Check Gmail API quota in Google Cloud Console

---

## Security Best Practices

1. **Never commit credentials**
   ```bash
   # Add to .gitignore
   token.json
   credential.json
   ```

2. **Use minimal scopes**
   - Currently using: readonly, send, compose
   - Don't add unnecessary permissions

3. **Rotate tokens periodically**
   - Delete `token.json` and re-authenticate every 90 days

4. **Monitor API usage**
   - Check Gmail API quota in Google Cloud Console

---

## Testing

### Test Authentication
```bash
python authenticate.py
# Should show: ✓ Authenticated as: your.email@gmail.com
```

### Test Watcher
```bash
# Send yourself a test email with "urgent" in subject
# Then run watcher
python gmail_watcher.py ../../../AI_Employee_Vault

# Check Needs_Action/ for new action file
```

### Test Email Sending
```bash
# After processing email, draft reply
qwen "Draft a reply to the test email"

# Move draft to Approved/
# Send it
python ../gmail-sender/scripts/send_email.py ../../../AI_Employee_Vault --action send
```

---

## Next Steps

After Gmail Watcher is working:
1. Set up LinkedIn Poster for social media
2. Configure scheduler for automated briefings
3. Set up approval workflow for sensitive actions

See `SILVER_TIER_COMPLETE.md` for full Silver Tier setup.
