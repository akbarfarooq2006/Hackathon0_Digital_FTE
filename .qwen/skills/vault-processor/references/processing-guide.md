# Vault Processor Reference

## File Processing Pipeline

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Inbox/         │────▶│   Watcher    │────▶│  Needs_Action/   │
│  (file drop)    │     │  (detects)   │     │  (action file)   │
└─────────────────┘     └──────────────┘     └──────────────────┘
                                                    │
                                                    ▼
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Done/          │◀────│   Claude     │◀────│  Dashboard.md    │
│  (completed)    │     │  (processes) │     │  (updated)       │
└─────────────────┘     └──────────────┘     └──────────────────┘
```

## Action File Types

### 1. File Drop
```markdown
---
type: file_drop
original_name: document.pdf
received: 2026-03-17T10:30:00
status: pending
---
```

### 2. Email
```markdown
---
type: email
from: client@example.com
subject: Invoice Request
received: 2026-03-17T10:30:00
priority: high
status: pending
---
```

### 3. Approval Request
```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---
```

### 4. Task
```markdown
---
type: task
description: Send invoice to Client B
priority: medium
due: 2026-03-20
status: pending
---
```

## Status Flow

```
pending → in_progress → completed → Done/
                      → pending_approval → Pending_Approval/
pending_approval → approved → Approved/ → executed → Done/
                 → rejected → Rejected/
```

## Priority Levels

| Priority | Response Time | Action |
|----------|---------------|--------|
| urgent | < 1 hour | Immediate processing, notify human |
| high | < 4 hours | Process next |
| medium | < 24 hours | Process in batch |
| low | < 7 days | Process when idle |

## Checklist for Processing

- [ ] Read Company_Handbook.md for rules
- [ ] Check Dashboard.md for context
- [ ] Read action file in Needs_Action/
- [ ] Determine required action
- [ ] Check if approval needed (payment > $500, sensitive)
- [ ] Execute action or create approval request
- [ ] Update Dashboard.md
- [ ] Move file to appropriate folder
