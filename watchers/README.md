# Watcher Scripts

Lightweight Python scripts that monitor inputs and create actionable files for Claude Code.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r ../requirements.txt
```

### 2. Run the File System Watcher

```bash
# Start the watcher (replace with your vault path)
python filesystem_watcher.py ../AI_Employee_Vault
```

### 3. Test It

1. Keep the watcher running in a terminal
2. Drop any file (e.g., `test.txt`) into the `AI_Employee_Vault/Inbox` folder
3. Watch the logs - it will create a `.md` action file in `Needs_Action`

## Available Watchers

| Watcher | Purpose | Tier |
|---------|---------|------|
| `filesystem_watcher.py` | Monitor Inbox folder for new files | Bronze |
| `gmail_watcher.py` | Monitor Gmail for new emails | Silver |
| `whatsapp_watcher.py` | Monitor WhatsApp for urgent messages | Silver |

## How It Works

```
┌─────────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Inbox Folder   │ ──► │   Watcher    │ ──► │  Needs_Action/   │
│  (file dropped) │     │  (detects)   │     │  (action file)   │
└─────────────────┘     └──────────────┘     └──────────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │   Claude Code    │
                                          │  (processes)     │
                                          └──────────────────┘
```

## Stopping the Watcher

Press `Ctrl+C` in the terminal to stop the watcher.

## Creating Your Own Watcher

1. Inherit from `BaseWatcher` in `base_watcher.py`
2. Implement `check_for_updates()` - return new items
3. Implement `create_action_file(item)` - create `.md` file
4. Call `watcher.run()` to start

See `filesystem_watcher.py` for a complete example.
