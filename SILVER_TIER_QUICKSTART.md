# Silver Tier - Quick Start Guide

## Overview

Silver Tier adds **communication monitoring** and **automated posting** to your AI Employee:

- 📧 **Gmail Watcher** - Monitor Gmail for new emails
- 💼 **LinkedIn Poster** - Auto-post business content
- 📝 **Plan Creator** - Multi-step task planning
- ✅ **Approval Workflow** - Human-in-the-loop controls
- 📅 **Scheduler** - Automated daily/weekly tasks
- 📤 **Gmail Sender** - Send/reply to emails

---

## Prerequisites

```bash
# Install all dependencies
cd E:\IT learning file\Projects\Agentic_project\AI_Employee\Hackathon0_Digital_FTE
pip install -r requirements.txt
```

---

## Step 1: Gmail Setup (10 minutes)

Your `secrets/credential.json` is already configured. Just need to authenticate:

### Authenticate with Gmail

```bash
cd .qwen/skills/gmail-watcher/scripts
python authenticate.py
```

**What happens:**
1. Browser opens
2. Sign in to Google
3. Grant Gmail API permissions
4. `token.json` saved

**Expected output:**
```
✓ Authenticated as: your.email@gmail.com
✓ Token saved to: token.json
```

### Test Gmail Watcher

```bash
# Send yourself a test email with "urgent" in subject

# Start watcher
python gmail_watcher.py ../../../AI_Employee_Vault

# Watch for output:
# "Created action file: EMAIL_*.md"
```

**Stop watcher:** Press `Ctrl+C`

---

## Step 2: LinkedIn Setup (5 minutes)

### Install Playwright

```bash
pip install playwright
playwright install chromium
```

### Test LinkedIn Poster

```bash
# Create a test post draft
cd ../../../
qwen "Create a LinkedIn post about completing Silver Tier"

# Check Pending_Approval/ for draft
# Review and move to Approved/

# Post it
cd .qwen/skills/linkedin-poster
python scripts/post_linkedin.py ../../../AI_Employee_Vault --action post
```

**Note:** First time may require manual LinkedIn login in browser.

---

## Step 3: Test Complete Workflow (10 minutes)

### Email → Reply Workflow

1. **Receive Email**
   - Send test email to your Gmail
   - Subject: "Test - AI Employee"

2. **Watcher Detects**
   ```bash
   python ../gmail-watcher/scripts/gmail_watcher.py ../../../AI_Employee_Vault
   # Creates: Needs_Action/EMAIL_*.md
   ```

3. **Qwen Drafts Reply**
   ```bash
   # In new terminal
   qwen "Draft a reply to the test email"
   # Creates: Pending_Approval/EMAIL_REPLY_*.md
   ```

4. **Approve & Send**
   ```
   - Move draft to Approved/
   python ../gmail-sender/scripts/send_email.py ../../../AI_Employee_Vault --action send
   ```

### LinkedIn Post Workflow

1. **Create Post**
   ```bash
   qwen "Create a LinkedIn post about AI automation"
   ```

2. **Approve**
   ```
   - Move from Pending_Approval/ to Approved/
   ```

3. **Post**
   ```bash
   python scripts/post_linkedin.py ../../../AI_Employee_Vault --action post
   ```

---

## Step 4: Configure Scheduler (Optional)

### Daily Briefing (Windows Task Scheduler)

```batch
:: Create batch file: daily_briefing.bat
@echo off
cd /d "E:\IT learning file\Projects\Agentic_project\AI_Employee\Hackathon0_Digital_FTE"
qwen "Generate daily briefing and update Dashboard.md"
```

**Schedule it:**
```bash
schtasks /create /tn "AI_Daily_Briefing" /tr "E:\path\to\daily_briefing.bat" /sc daily /st 08:00
```

### Weekly CEO Briefing

```batch
:: weekly_briefing.bat
@echo off
cd /d "E:\IT learning file\Projects\Agentic_project\AI_Employee\Hackathon0_Digital_FTE"
qwen "Generate weekly CEO briefing from Done/ and Business_Goals.md"
```

**Schedule it:**
```bash
schtasks /create /tn "AI_Weekly_Briefing" /tr "E:\path\to\weekly_briefing.bat" /sc weekly /d SUN /st 22:00
```

---

## Silver Tier Checklist

### Communication Watchers
- [ ] Gmail Watcher authenticated
- [ ] Gmail Watcher tested with real email
- [ ] Action files created in Needs_Action/
- [ ] LinkedIn Poster installed
- [ ] Test post created and published

### Email Sending
- [ ] Gmail Sender tested
- [ ] Reply workflow working
- [ ] Approval workflow tested

### Planning & Scheduling
- [ ] Plan Creator tested
- [ ] Daily briefing scheduled
- [ ] Weekly briefing scheduled

### Documentation
- [ ] All skills documented
- [ ] Credentials secured (not committed)
- [ ] Token files in .gitignore

---

## Troubleshooting

### Gmail Authentication Failed

**Check:**
1. `secrets/credential.json` exists in project root
2. Gmail API enabled in Google Cloud Console
3. OAuth consent screen configured

**Re-authenticate:**
```bash
rm token.json
python authenticate.py
```

### LinkedIn Post Failed

**Check:**
1. Playwright installed: `playwright install chromium`
2. Browser session active
3. LinkedIn account accessible

**Manual login:**
```bash
# Browser will open for manual login
python scripts/post_linkedin.py ../../../AI_Employee_Vault --action post
```

### Watcher Not Detecting Emails

**Check:**
1. No unread emails
2. Gmail API quota not exceeded
3. Correct OAuth scopes

**Test:**
```bash
# Send email with "urgent" subject
# Restart watcher
python gmail_watcher.py ../../../AI_Employee_Vault
```

---

## Next Steps (Gold Tier)

After Silver Tier is working:

1. **Odoo Accounting Integration**
   - Self-hosted Odoo Community
   - MCP server for invoices/payments

2. **Social Media Expansion**
   - Facebook/Instagram integration
   - Twitter (X) posting

3. **Enhanced Automation**
   - Ralph Wiggum loop for autonomy
   - Error recovery
   - Comprehensive logging

4. **Weekly Business Audit**
   - Revenue tracking
   - Bottleneck analysis
   - Proactive suggestions

---

## Support Files

| File | Purpose |
|------|---------|
| `secrets/credential.json` | Google OAuth credentials |
| `token.json` | Gmail OAuth token (auto-generated) |
| `.env` | Environment configuration |
| `requirements.txt` | Python dependencies |
| `SILVER_TIER_COMPLETE.md` | Full documentation |

---

## Security Reminders

1. **Never commit:**
   - `token.json`
   - `.env`
   - `secrets/credential.json`

2. **Add to `.gitignore`:**
   ```
   token.json
   .env
   secrets/
   *.log
   ```

3. **Rotate tokens** every 90 days

4. **Monitor API usage** in Google Cloud Console

---

**Ready to build your Silver Tier AI Employee!** 🚀

For detailed documentation, see:
- Gmail Watcher: `.qwen/skills/gmail-watcher/references/SETUP.md`
- LinkedIn Poster: `.qwen/skills/linkedin-poster/SKILL.md`
- Gmail Sender: `.qwen/skills/gmail-sender/references/USAGE_GUIDE.md`
