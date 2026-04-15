# 🤖 Digital FTE: AI Employee (Silver Tier)

> **"Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop."**

This project is a comprehensive implementation of a **Digital FTE (Full-Time Equivalent)** as envisioned in the [AI Employee Hackathon 0](AI_Employee_Hackathon0.md). It leverages **Claude Code** (the brain), **Obsidian** (the memory/GUI), and **Python Watchers** (the senses) to create a proactive, autonomous business partner.

---

## 🚀 Silver Tier Status: COMPLETE ✅

This project has successfully met all **Silver Tier** requirements, transforming from a simple foundation into a functional assistant capable of managing communications and social presence autonomously.

### Key Silver Tier Features:
- **Multi-Sense Perception**: Active watchers for Gmail, WhatsApp, LinkedIn, and the local file system.
- **Automated Social Presence**: Intelligent LinkedIn posting with AI-generated content and human-in-the-loop approval.
- **Bi-directional Email**: Automated Gmail monitoring with drafting and sending capabilities via Google OAuth.
- **Centralized Orchestration**: A master `orchestrator.py` that manages all background tasks, schedules, and folder watching.
- **Human-in-the-Loop (HITL)**: Secure approval workflow for sensitive actions (sending emails, posting to social media).
- **Proactive Planning**: Automatic generation of `Plan.md` files for complex multi-step tasks.

---

## 🏗️ Architecture

- **The Brain (Claude Code/Qwen)**: The reasoning engine that processes tasks and interacts with the vault.
- **The Memory (Obsidian Vault)**: A local-first markdown database (`/AI_Employee_Vault`) acting as the long-term memory and user interface.
- **The Senses (Watchers)**: Python scripts monitoring input channels (Gmail, WhatsApp, Files) and populating `/Needs_Action`.
- **The Hands (MCP Skills)**: Specialized skills in `.qwen/skills/` that extend AI capabilities (browser control, email sending, social posting).
- **The Heart (Orchestrator)**: `orchestrator.py` manages the continuous lifecycle of the AI Employee.

---

## 🛠️ Project Structure

```text
.
├── AI_Employee_Vault/       # 📂 The Obsidian Vault (GUI & Memory)
│   ├── Needs_Action/        # 📥 Incoming tasks from watchers
│   ├── Pending_Approval/    # ⏳ Drafts waiting for human review
│   ├── Approved/            # ✅ Confirmed actions ready for execution
│   ├── Done/                # 🏁 Archive of completed tasks
│   └── Briefings/           # 📊 Logs and success reports
├── .qwen/skills/            # 🧠 AI Agent Skills (MCP)
│   ├── gmail-watcher/       # 📧 Monitors Gmail API
│   ├── linkedin-poster/     # 🔗 Playwright-based LinkedIn automation
│   ├── whatsapp-watcher/    # 💬 WhatsApp Web monitoring
│   └── ...                  # Other core skills (9 total)
├── watchers/                # 👁️ Sensory scripts
├── data/                    # 💾 Persistent sessions and tokens
├── orchestrator.py          # ⚙️ Master process/Glue
└── AI_Employee_Hackathon0.md # 📜 Blueprint & Blueprint
```

---

## 🏁 Installation & Setup

### 1. Prerequisites
- **Python 3.13+**
- **Node.js v24+**
- **Obsidian** (to use as a dashboard)
- **Claude Code** or compatible router

### 2. Core Installation
```bash
# Clone the repository
git clone https://github.com/akbarfarooq2006/Hackathon0_Digital_FTE.git
cd Hackathon0_Digital_FTE

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (for LinkedIn & Browser tools)
playwright install chromium
```

### 3. Service Authentication 🔑
Before running the orchestrator, you must authenticate the services.

#### A. Gmail Authentication
Place your Google Cloud `credentials.json` in the `/secrets` folder and run:
```bash
cd .qwen/skills/gmail-watcher/scripts
python authenticate.py
```
*Note: Once authenticated, your secure access token will be stored in `data/gmail_token.json`.*

#### B. LinkedIn Authentication
LinkedIn requires a manual login once to save a persistent browser session.
```bash
cd .qwen/skills/linkedin-poster/scripts
python authenticate_linkedin.py
```
*Note: A browser will open. Log in normally, and the script will save your session to `data/.linkedin_session`.*

---

## ⚙️ Orchestrator: The Heart of the System

The `orchestrator.py` is the master process that runs in the background. It manages watchers, schedules, and the communication loop between the AI and your vault.

### Starting the Employee
From the project root, run:
```bash
python orchestrator.py
```

### Typical Workflow
1. **Senses**: A **Watcher** detects a new email or LinkedIn prompt and creates a file in `Needs_Action/`.
2. **Reasoning**: The **Orchestrator** triggers Qwen to draft a response/post in `Pending_Approval/`.
3. **HITL Review**: You review and modify the markdown file in Obsidian.
4. **Approval**: You move the file to `Approved/`.
5. **Action**: The **Orchestrator** detects the move and executes the relevant **Skill**.
6. **Logging**: The task is moved to `Done/` and success is logged in `Briefings/`.

---

## 🔐 Security & Privacy
- **Local First**: Your data stays in your Obsidian vault.
- **Sandbox Mode**: Use `.env` flags for testing without hitting real APIs.
- **No Plaintext Secrets**: All tokens (`token.json`, sessions) are git-ignored.
- **HITL Verification**: Critical actions *require* your manual move to the `Approved/` folder.

---

## 📜 Complete Skill Inventory (9)
| Tier | Skill | Purpose |
|------|-------|---------|
| **Bronze** | `vault-processor` | Core file system management |
| **Bronze** | `browsing-with-playwright` | Web navigation & automation |
| **Silver** | `gmail-watcher` | Real-time email monitoring |
| **Silver** | `gmail-sender` | OAuth-secured email delivery |
| **Silver** | `linkedin-poster` | AI content & Playwright posting |
| **Silver** | `whatsapp-watcher` | Message monitoring |
| **Silver** | `plan-creator` | Task breakdown & roadmapping |
| **Silver** | `approval-workflow` | Managed HITL logic |
| **Silver** | `scheduler` | Task timing & cron management |

---

## 📈 Roadmap (Next: Gold Tier)
- [ ] **Odoo ERP Integration**: Full accounting and invoicing automation.
- [ ] **Cross-Social Sync**: Facebook, Instagram, and Twitter (X) presence.
- [ ] **Ralph Wiggum Loop**: Full autonomy with self-correction logic.
- [ ] **Weekly CEO Briefings**: Automated business audit and revenue reporting.

---

**Developed for the AI Employee Hackathon 0 | 2026**
*Tagline: Hire an AI that doesn't just chat, but works.*
