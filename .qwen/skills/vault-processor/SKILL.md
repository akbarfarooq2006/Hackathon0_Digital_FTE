---
name: vault-processor
description: |
  Process files in the AI Employee Obsidian vault. Read from Inbox/Needs_Action,
  process content using Claude Code reasoning, update Dashboard, and move completed
  tasks to Done. Core skill for AI Employee Bronze Tier functionality.
---

# Vault Processor Skill

Process files and tasks in the AI Employee Obsidian vault using Claude Code.

## Vault Structure

```
AI_Employee_Vault/
├── Dashboard.md           # Main dashboard (read/write)
├── Company_Handbook.md    # Rules and guidelines (read)
├── Inbox/                 # Drop folder for new files
├── Needs_Action/          # Items requiring processing
├── Done/                  # Completed tasks
├── Pending_Approval/      # Awaiting human approval
├── Approved/              # Approved actions ready for execution
├── Briefings/             # CEO briefings and reports
├── Accounting/            # Financial records
└── Plans/                 # Task plans
```

## Quick Start

### Process All Pending Items

```bash
claude "Check /Needs_Action folder and process all pending items according to Company_Handbook rules"
```

### Update Dashboard

```bash
claude "Read all vault files and update Dashboard.md with current status"
```

### Generate Briefing

```bash
claude "Generate a weekly briefing based on completed tasks in /Done"
```

## Workflow: Process File Drop

1. **Watcher detects** new file in `Inbox/`
2. **Watcher creates** `.md` action file in `Needs_Action/`
3. **Claude reads** the action file
4. **Claude processes** according to Company_Handbook rules
5. **Claude moves** file to `Done/` when complete
6. **Claude updates** Dashboard.md

## Workflow: Handle Sensitive Actions

For sensitive actions (payments, external communications):

1. **Create approval request** in `Pending_Approval/`:
   ```markdown
   ---
   type: approval_request
   action: payment
   amount: 500.00
   status: pending
   ---
   
   ## To Approve
   Move this file to /Approved folder.
   
   ## To Reject
   Move this file to /Rejected folder.
   ```

2. **Wait for human** to move file to `Approved/`
3. **Execute action** after approval
4. **Move to Done** and log

## Company Handbook Rules

Always follow these rules from Company_Handbook.md:

### Communication Rules
- Always be polite and professional
- Respond to urgent messages within 1 hour
- Flag messages containing "urgent", "asap", "emergency"

### Financial Rules
- Flag any payment over $500 for human approval
- Never initiate payments without explicit approval
- Log all transactions in /Accounting

### Task Processing Rules
- Process all files in /Needs_Action folder
- Move completed tasks to /Done folder
- Create approval requests for sensitive actions
- Never delete files - archive them

## Dashboard Update Template

```markdown
---
last_updated: {timestamp}
status: active
---

# AI Employee Dashboard

## Quick Status
| Metric | Value |
|--------|-------|
| Pending Tasks | {count} |
| Awaiting Approval | {count} |
| Completed Today | {count} |

## Recent Activity
{list recent completions}
```

## Action File Template

```markdown
---
type: file_drop
original_name: {filename}
received: {timestamp}
status: pending
---

# File Dropped for Processing

## File Information
- **Original Name:** {filename}
- **File Type:** {type}
- **Size:** {size}

## Suggested Actions
- [ ] Review file contents
- [ ] Process and extract information
- [ ] Take appropriate action
- [ ] Move to /Done when complete
```

## Commands Reference

| Command | Purpose |
|---------|---------|
| `claude "Process Needs_Action"` | Process all pending items |
| `claude "Update Dashboard"` | Refresh dashboard status |
| `claude "Generate briefing"` | Create weekly report |
| `claude "Check approvals"` | Process approved actions |

## Error Handling

- **File not found:** Log error, skip to next item
- **Permission denied:** Create approval request
- **Unknown action:** Flag for human review
- **Processing error:** Log details, move to /Needs_Action/_errors/

## Best Practices

1. **Read Company_Handbook.md first** - understand rules before acting
2. **Check Dashboard.md** - avoid duplicate processing
3. **Log all actions** - create audit trail in action files
4. **Request approval** - for any sensitive or financial actions
5. **Update Dashboard** - keep status current after each operation
