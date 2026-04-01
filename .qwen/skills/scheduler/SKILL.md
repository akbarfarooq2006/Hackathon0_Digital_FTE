---
name: scheduler
description: |
  Schedule recurring tasks and reminders using cron (Linux/Mac) or Task Scheduler (Windows).
  Creates scheduled tasks for daily briefings, weekly audits, periodic checks, and reminders.
  Use this skill when user mentions scheduling, cron, Task Scheduler, recurring tasks, 
  daily briefings, weekly audits, or automated reminders.
---

# Scheduler Skill

Schedule recurring tasks for the AI Employee.

## Supported Schedulers

| OS | Scheduler | Command |
|----|-----------|---------|
| Linux/Mac | cron | `crontab -e` |
| Windows | Task Scheduler | `schtasks.exe` |
| Cross-platform | Python schedule | `pip install schedule` |

## Usage

### Schedule Daily Briefing (8 AM)

```bash
# Linux/Mac
0 8 * * * claude "Generate daily briefing and update Dashboard.md"

# Windows
schtasks /create /tn "AI_Employee_Daily_Briefing" /tr "claude 'Generate daily briefing'" /sc daily /st 08:00
```

### Schedule Weekly Audit (Sunday 10 PM)

```bash
# Linux/Mac
0 22 * * 0 claude "Generate weekly CEO briefing from Done/ folder"

# Windows
schtasks /create /tn "AI_Employee_Weekly_Audit" /tr "claude 'Generate weekly briefing'" /sc weekly /d SUN /st 22:00
```

### Schedule Watcher Health Check (Every Hour)

```bash
# Linux/Mac
0 * * * * python /path/to/watchers/check_health.py

# Windows
schtasks /create /tn "AI_Employee_Health_Check" /tr "python C:\path\to\check_health.py" /sc hourly
```

## Common Schedules

### Daily Tasks
| Time | Task | Command |
|------|------|---------|
| 8:00 AM | Morning briefing | `claude "Generate daily briefing"` |
| 12:00 PM | Check approvals | `claude "Check Approved/ folder"` |
| 6:00 PM | End of day summary | `claude "Update Dashboard with today's progress"` |

### Weekly Tasks
| Day | Time | Task |
|-----|------|------|
| Monday | 9:00 AM | Weekly planning |
| Friday | 5:00 PM | Week review |
| Sunday | 10:00 PM | CEO briefing |

### Monthly Tasks
| Day | Task |
|-----|------|
| 1st | Monthly report |
| 15th | Mid-month review |
| Last | Subscription audit |

## Scripts

### check_health.py
```python
#!/usr/bin/env python3
"""Check if watchers are running and vault is healthy."""
import subprocess
import sys

def check_watcher_processes():
    """Check if watcher processes are running."""
    result = subprocess.run(
        ['pgrep', '-f', 'watcher'],
        capture_output=True, text=True
    )
    return bool(result.stdout.strip())

def check_vault_health():
    """Check vault folder structure."""
    from pathlib import Path
    vault = Path('./AI_Employee_Vault')
    required = ['Inbox', 'Needs_Action', 'Done', 'Pending_Approval']
    return all((vault / f).exists() for f in required)

if __name__ == '__main__':
    watcher_ok = check_watcher_processes()
    vault_ok = check_vault_health()
    
    if not watcher_ok:
        print("WARNING: Watcher processes not running!")
    if not vault_ok:
        print("WARNING: Vault structure incomplete!")
    
    sys.exit(0 if (watcher_ok and vault_ok) else 1)
```

## Setup Instructions

### Linux/Mac (cron)

1. Open crontab editor:
   ```bash
   crontab -e
   ```

2. Add schedule entries

3. Verify:
   ```bash
   crontab -l
   ```

### Windows (Task Scheduler)

1. Open Task Scheduler:
   ```bash
   taskschd.msc
   ```

2. Create Basic Task → Follow wizard

3. Or use command line:
   ```bash
   schtasks /create /tn "TaskName" /tr "command" /sc daily /st 08:00
   ```

4. Verify:
   ```bash
   schtasks /query /tn "TaskName"
   ```

## Environment Setup

For scheduled tasks to work:

1. **Claude Code** must be in PATH
2. **Python** must be in PATH  
3. **Vault path** must be absolute
4. **Credentials** must be available to scheduled user

### Example: Windows Batch File

```batch
@echo off
cd /d "E:\Projects\AI_Employee"
call claude "Generate daily briefing" >> logs/daily_briefing.log 2>&1
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Task not running | Check user permissions |
| Claude not found | Use absolute path to claude |
| Vault not accessible | Use absolute vault path |
| No logs | Redirect stdout/stderr to file |

## Integration

Works with:
- **vault-processor**: Generate briefings
- **gmail-watcher**: Periodic email checks
- **approval-workflow**: Scheduled approval reviews
