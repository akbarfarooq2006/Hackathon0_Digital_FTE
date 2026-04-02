---
name: plan-creator
description: |
  Create structured Plan.md files for multi-step tasks. Analyzes tasks in Needs_Action/,
  breaks them into actionable steps with checkboxes, tracks progress, and updates status.
  Use this skill when Qwen needs to plan complex multi-step tasks or when user mentions
  creating a plan, breaking down tasks, or step-by-step execution.
---

# Plan Creator Skill

Create and manage structured plans for multi-step tasks.

## Plan File Format

```markdown
---
type: plan
created: 2026-03-30T10:30:00Z
status: in_progress
priority: high
related_to: EMAIL_20260330_client_request.md
---

# Plan: Respond to Client Invoice Request

## Objective
Send invoice to client within 24 hours.

## Steps
- [x] Read email from client
- [x] Calculate amount due ($1,500)
- [ ] Generate invoice PDF
- [ ] Review invoice for accuracy
- [ ] Send invoice via email
- [ ] Log to Accounting folder
- [ ] Mark email as done

## Progress
3/7 steps complete (43%)

## Notes
- Client requested urgent invoice
- Amount: $1,500 for Project Alpha milestone 2
```

## Usage

### Create Plan

```bash
qwen "Create a plan for responding to the client invoice request"
```

### Update Plan Progress

```bash
qwen "Update plan status - completed steps 3 and 4"
```

### Review Plans

```bash
qwen "Review all active plans in Plans/ folder"
```

## Workflow

```
Task detected in Needs_Action/
       ↓
Is it multi-step?
       ↓
YES: Create Plan.md
       ↓
Execute steps one by one
       ↓
Update progress after each step
       ↓
When all done → Move to Done/
```

## Plan Templates

### Email Response Plan
```markdown
## Steps
- [ ] Read original message
- [ ] Draft response
- [ ] Review for tone and accuracy
- [ ] Send (or create approval request)
- [ ] Archive original
```

### Payment Plan
```markdown
## Steps
- [ ] Verify invoice details
- [ ] Check available funds
- [ ] Create approval request (if > $500)
- [ ] Wait for approval
- [ ] Execute payment
- [ ] Log transaction
```

### Content Creation Plan
```markdown
## Steps
- [ ] Research topic
- [ ] Draft content
- [ ] Review and edit
- [ ] Create approval request
- [ ] Schedule/post after approval
- [ ] Log to Briefings/
```

## Status Values

| Status | Meaning |
|--------|---------|
| `pending` | Plan created, not started |
| `in_progress` | Steps being executed |
| `blocked` | Waiting on external factor |
| `completed` | All steps done |
| `cancelled` | Plan abandoned |

## Integration

Works with:
- **vault-processor**: Read/write plan files
- **approval-workflow**: Create approvals for sensitive steps
- **scheduler**: Schedule plan execution

## Best Practices

1. **One plan per task** - Keep plans focused
2. **Clear objectives** - State what success looks like
3. **Actionable steps** - Each step should be executable
4. **Track progress** - Update after each step
5. **Archive when done** - Move to Done/ folder
