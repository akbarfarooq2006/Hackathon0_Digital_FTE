---
name: approval-workflow
description: |
  Human-in-the-loop approval workflow for sensitive actions. Creates approval request files 
  in Pending_Approval/, waits for human to move to Approved/ or Rejected/, then executes 
  or cancels the action. Use for payments, external communications, or any sensitive operations.
  Triggers when user mentions approval workflow, sensitive actions, payment approval, 
  human-in-the-loop, or moving files between approval folders.
---

# Approval Workflow Skill

Human-in-the-loop approval system for sensitive actions.

## Vault Folders

```
AI_Employee_Vault/
├── Pending_Approval/    ← New approval requests go here
├── Approved/            ← Human moves here to approve
├── Rejected/            ← Human moves here to reject
└── Done/                ← Completed approvals archived here
```

## Approval Request Format

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
reason: Invoice #1234 payment
created: 2026-03-30T10:30:00Z
expires: 2026-03-31T10:30:00Z
status: pending
---

# Approval Required: Payment

## Details
- **Action:** Payment
- **Amount:** $500.00
- **Recipient:** Client A (Bank: XXXX1234)
- **Reason:** Invoice #1234 payment

## To Approve
Move this file to `/Approved` folder.

## To Reject
Move this file to `/Rejected` folder.

## Notes
<!-- Claude will add context here -->
```

## Workflow

```
Claude detects sensitive action
       ↓
Create approval request in Pending_Approval/
       ↓
Wait for human decision
       ↓
┌──────┴──────┐
│             │
▼             ▼
Approved/     Rejected/
│             │
▼             ▼
Execute       Archive
│
▼
Move to Done/
```

## Usage

### Create Approval Request

```bash
claude "Create approval request for $500 payment to Client A for Invoice #1234"
```

### Check Pending Approvals

```bash
claude "Check Pending_Approval folder for items awaiting review"
```

### Process Approved Items

```bash
claude "Process all approved items in Approved/ folder"
```

## Approval Rules (from Company_Handbook.md)

| Action | Threshold | Requires Approval |
|--------|-----------|-------------------|
| Payment | Any amount | > $500 |
| External Email | Sensitive content | Always |
| Social Media Post | Public post | Always |
| Calendar Event | Meeting with external | > $100 cost |

## Scripts

| Script | Purpose |
|--------|---------|
| `check_approvals.py` | Monitor Approved/Rejected folders |
| `create_approval.py` | Create new approval requests |

## Integration

Works with:
- **vault-processor**: Move files between folders
- **email-sender**: Send after approval
- **payment-mcp**: Execute payments after approval

## Best Practices

1. **Always create approval** for sensitive actions
2. **Include full context** in approval request
3. **Set reasonable expiry** (24-48 hours)
4. **Log all actions** after execution
5. **Archive to Done/** after completion
