# AI Employee Hackathon 0: Digital FTE - Project Context

## Project Overview

This project is a **hackathon blueprint** for building a "Digital FTE" (Full-Time Equivalent) — an autonomous AI employee powered by **Claude Code** and **Obsidian**. The AI agent proactively manages personal and business affairs 24/7 using a local-first, agent-driven architecture.

### Core Architecture

| Layer | Component | Purpose |
|-------|-----------|---------|
| **Brain** | Claude Code | Reasoning engine for decision-making |
| **Memory/GUI** | Obsidian (Markdown) | Dashboard and long-term memory storage |
| **Senses (Watchers)** | Python scripts | Monitor Gmail, WhatsApp, filesystems to trigger AI |
| **Hands (MCP)** | Model Context Protocol servers | External actions (email, browser automation, payments) |

### Key Features

- **Watcher Architecture**: Lightweight Python scripts continuously monitor inputs and create actionable `.md` files in `/Needs_Action` folders
- **Ralph Wiggum Loop**: A Stop hook pattern that keeps Claude iterating until multi-step tasks are complete
- **Human-in-the-Loop**: Sensitive actions require approval via file movement (`/Pending_Approval` → `/Approved`)
- **Monday Morning CEO Briefing**: Autonomous weekly audit generating revenue reports and bottleneck analysis

## Project Structure

```
Hackathon0_Digital_FTE/
├── AI_Employee_Hackathon0.md    # Main hackathon blueprint (1200+ lines)
├── README.md                     # Project readme
├── .env.example                  # Environment variable template
├── skills-lock.json              # Installed skill dependencies
└── .qwen/skills/
    └── browsing-with-playwright/ # Browser automation skill
        ├── SKILL.md              # Skill documentation
        ├── scripts/
        │   ├── mcp-client.py     # Universal MCP client (HTTP + stdio)
        │   ├── start-server.sh   # Start Playwright MCP server
        │   ├── stop-server.sh    # Stop Playwright MCP server
        │   └── verify.py         # Server health check
        └── references/
            └── playwright-tools.md  # 22 available browser tools
```

## Building and Running

### Prerequisites

| Component | Version | Purpose |
|-----------|---------|---------|
| Claude Code | Active subscription | Primary reasoning engine |
| Obsidian | v1.10.6+ | Knowledge base & dashboard |
| Python | 3.13+ | Watcher scripts & orchestration |
| Node.js | v24+ LTS | MCP servers & automation |
| GitHub Desktop | Latest | Version control |

### Setup Commands

```bash
# 1. Create Obsidian vault
mkdir AI_Employee_Vault
cd AI_Employee_Vault
mkdir Inbox Needs_Action Done Pending_Approval Approved

# 2. Verify Claude Code installation
claude --version

# 3. Install Playwright MCP server (for browser automation)
npx @playwright/mcp@latest --port 8808 --shared-browser-context &

# 4. Verify MCP server
python .qwen/skills/browsing-with-playwright/scripts/verify.py

# 5. Set up environment variables
cp .env.example .env
# Edit .env with your API credentials
```

### Starting the Playwright MCP Server

```bash
# Start server (recommended)
bash .qwen/skills/browsing-with-playwright/scripts/start-server.sh

# Or manually
npx @playwright/mcp@latest --port 8808 --shared-browser-context &

# Stop server
bash .qwen/skills/browsing-with-playwright/scripts/stop-server.sh
```

### Using the MCP Client

```bash
# List available tools
python .qwen/skills/browsing-with-playwright/scripts/mcp-client.py list -u http://localhost:8808

# Call a tool (navigate to URL)
python .qwen/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_navigate \
  -p '{"url": "https://example.com"}'

# Take a screenshot
python .qwen/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_take_screenshot \
  -p '{"type": "png", "fullPage": true}'

# Get page snapshot (for element interaction)
python .qwen/skills/browsing-with-playwright/scripts/mcp-client.py call \
  -u http://localhost:8808 \
  -t browser_snapshot \
  -p '{}'
```

### Ralph Wiggum Loop (Persistence Pattern)

```bash
# Start a Ralph loop for autonomous task completion
/ralph-loop "Process all files in /Needs_Action, move to /Done when complete" \
  --completion-promise "TASK_COMPLETE" \
  --max-iterations 10
```

## Development Conventions

### File-Based Communication

All inter-component communication happens via Markdown files:

| Folder | Purpose |
|--------|---------| 
| `AI_Employee_Vault/Inbox` | Raw incoming data |
| `AI_Employee_Vault/Needs_Action` | Items requiring AI processing |
| `AI_Employee_Vault/Pending_Approval` | Actions awaiting human approval |
| `AI_Employee_Vault/Approved` | Approved actions ready for execution |
| `AI_Employee_Vault/Done` | Completed tasks |
| `AI_Employee_Vault/Briefings` | CEO briefings and reports |
| `AI_Employee_Vault/Plans` | Step-by-step task plans with checkboxes |

### Watcher Script Pattern

All Watchers follow this base structure:

```python
from base_watcher import BaseWatcher
from pathlib import Path

class MyWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        '''Return list of new items to process'''
        pass

    def create_action_file(self, item) -> Path:
        '''Create .md file in Needs_Action folder'''
        pass
```

### Human-in-the-Loop Pattern

For sensitive actions, Claude writes an approval request file instead of acting directly:

```markdown
---
type: approval_request
action: payment
amount: 500.00
recipient: Client A
status: pending
---

## To Approve
Move this file to /Approved folder.

## To Reject
Move this file to /Rejected folder.
```

## Available Browser Tools (Playwright MCP)

The `browsing-with-playwright` skill provides **22 tools**:

| Category | Tools |
|----------|-------|
| **Navigation** | `browser_navigate`, `browser_navigate_back`, `browser_tabs` |
| **Interaction** | `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option`, `browser_drag`, `browser_hover`, `browser_press_key` |
| **State** | `browser_snapshot`, `browser_take_screenshot`, `browser_console_messages`, `browser_network_requests` |
| **Advanced** | `browser_evaluate`, `browser_run_code`, `browser_wait_for`, `browser_handle_dialog`, `browser_file_upload` |
| **Lifecycle** | `browser_close`, `browser_install`, `browser_resize` |

## Hackathon Tiers

| Tier | Time | Deliverables |
|------|------|--------------|
| **Bronze** | 8-12 hours | Obsidian vault, one Watcher, basic folder structure |
| **Silver** | 20-30 hours | Multiple Watchers, MCP server, approval workflow, scheduling |
| **Gold** | 40+ hours | Full integration, Odoo accounting, social media, Ralph Wiggum loop |
| **Platinum** | 60+ hours | Cloud deployment, dual-agent (Cloud/Local), A2A upgrade |

## Key URLs & Resources

- **Zoom Meetings**: Wednesdays 10:00 PM - [Join Link](https://us06web.zoom.us/j/87188707642?pwd=a9XloCsinvn1JzICbPc2YGUvWTbOTr.1)
- **YouTube**: [Panaversity Channel](https://www.youtube.com/@panaversity)
- **Ralph Wiggum Reference**: [GitHub](https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum)
- **Agent Skills Documentation**: [Claude Platform](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- **MCP Servers**: [Model Context Protocol](https://github.com/AlanOgic/mcp-odoo-adv)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Playwright MCP not responding | Run `bash scripts/stop-server.sh && bash scripts/start-server.sh` |
| Element not found | Run `browser_snapshot` first to get current refs |
| Click fails | Try `browser_hover` first, then click |
| Server process errors | Check `pgrep -f "@playwright/mcp"` for running process |
| Ralph loop not completing | Ensure task file moves to `/Done` or output contains completion promise |

## Security Notes

- **Never commit `.env` files** - Contains API keys and credentials
- **Vault sync excludes secrets** - Only markdown/state files sync; tokens and sessions stay local
- **Human approval required** - Payment and sensitive actions always require manual approval
