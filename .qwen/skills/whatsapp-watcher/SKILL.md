---
name: whatsapp-watcher
description: |
  Monitor WhatsApp Web for new messages containing urgent keywords. Uses Playwright 
  browser automation to detect unread messages and creates action files in Needs_Action/.
  Use this skill when setting up WhatsApp monitoring for the AI Employee Silver Tier.
  Triggers when user mentions WhatsApp monitoring, WhatsApp watcher, or checking WhatsApp messages.
---

# WhatsApp Watcher Skill

Monitor WhatsApp Web for urgent messages and create actionable files.

## Prerequisites

```bash
pip install playwright
playwright install chromium
```

## Configuration

### Environment Variables (.env)
```bash
WHATSAPP_SESSION_PATH=./.whatsapp_session
VAULT_PATH=./AI_Employee_Vault
CHECK_INTERVAL=30
KEYWORDS=urgent,asap,invoice,payment,help
```

## Usage

### Start Watcher
```bash
cd .qwen/skills/whatsapp-watcher
python scripts/whatsapp_watcher.py ../../AI_Employee_Vault
```

### First-Time Setup
1. Run the watcher
2. Scan QR code with WhatsApp mobile app
3. Session saved for future runs

## Action File Format

Creates file in `Needs_Action/`:

```markdown
---
type: whatsapp_message
from: +1234567890
chat: John Doe
received: 2026-03-30T10:30:00
priority: high
status: pending
keywords: urgent, invoice
---

# WhatsApp Message

## From
John Doe (+1234567890)

## Received
2026-03-30 10:30 AM

## Message
Hi, I need the invoice urgently!

## Suggested Actions
- [ ] Reply to sender
- [ ] Take appropriate action
- [ ] Mark as read
```

## Keyword Detection

Default keywords: `urgent`, `asap`, `invoice`, `payment`, `help`, `emergency`

Customize with `--keywords` flag:
```bash
python scripts/whatsapp_watcher.py ../Vault --keywords "urgent,asap,billing,help"
```

## Workflow

```
WhatsApp Web (poll every 30s)
       ↓
Unread message with keywords?
       ↓
Create action file in Needs_Action/
       ↓
Claude Code processes message
       ↓
Reply/Take action
       ↓
Mark as processed
```

## Security Notes

- Session data stored locally in `.whatsapp_session/`
- Never commit session files to git
- WhatsApp Web requires phone connection
- Respect WhatsApp Terms of Service

## Troubleshooting

| Issue | Solution |
|-------|----------|
| QR code not showing | Delete session folder, restart |
| No messages detected | Check keywords, ensure unread messages exist |
| Browser crashes | Update Playwright: `pip install -U playwright` |

## Integration

Works with:
- **vault-processor**: Process message action files
- **browsing-with-playwright**: Send replies via WhatsApp Web
- **approval-workflow**: Flag sensitive messages
