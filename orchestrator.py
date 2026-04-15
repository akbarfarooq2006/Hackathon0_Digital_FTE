#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Orchestrator - Master process for AI Employee Silver Tier.

Handles:
1. Folder watching (Needs_Action, Approved, Rejected)
2. Scheduled tasks (Qwen triggers, LinkedIn posts, Business audits)
3. Qwen Code execution
4. MCP actions (email sending)
5. Logging

Usage:
    python orchestrator.py [--vault-path PATH]
"""

import sys
import os
import time
import json
import shutil
import logging
import argparse
import subprocess
from pathlib import Path
from datetime import datetime

# Third-party imports
try:
    import schedule
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install watchdog schedule")
    sys.exit(1)


class OrchestratorLogger:
    """Logger that writes to both console and vault log file."""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('orchestrator')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        fh = logging.FileHandler(str(log_path))
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        self.logger.addHandler(fh)
        self.logger.addHandler(ch)
    
    def log(self, message: str):
        self.logger.info(message)
    
    def log_error(self, message: str):
        self.logger.error(message)


class FolderHandler(FileSystemEventHandler):
    """Watchdog handler for vault folder changes."""
    
    def __init__(self, folder_name: str, orchestrator):
        self.folder_name = folder_name
        self.orchestrator = orchestrator
    
    def on_created(self, event):
        if event.is_directory:
            return
        filepath = Path(event.src_path)
        if filepath.suffix == '.md':
            self.orchestrator.logger.log(f"New file detected in {self.folder_name}: {filepath.name}")
            
            if self.folder_name == 'Needs_Action':
                self.orchestrator.process_needs_action(filepath)
            elif self.folder_name == 'Approved':
                self.orchestrator.process_approved(filepath)
            elif self.folder_name == 'Rejected':
                self.orchestrator.process_rejected(filepath)


class Orchestrator:
    """Main orchestrator for AI Employee."""
    
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.needs_action = vault_path / 'Needs_Action'
        self.approved = vault_path / 'Approved'
        self.rejected = vault_path / 'Rejected'
        self.done = vault_path / 'Done'
        self.plans = vault_path / 'Plans'
        self.logs = vault_path / 'Logs'
        self.pending_approval = vault_path / 'Pending_Approval'
        
        # Ensure folders exist
        for folder in [self.needs_action, self.approved, self.rejected, 
                       self.done, self.plans, self.logs, self.pending_approval]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = OrchestratorLogger(self.logs / 'orchestrator_log.md')
        self.logger.log("=" * 60)
        self.logger.log("Orchestrator started")
        self.logger.log(f"Vault path: {self.vault_path}")
        self.logger.log("=" * 60)
        
        # Track processed files to avoid duplicates
        self.processed_files = set()
    
    def run_qwen_code(self, prompt: str, timeout: int = 300) -> tuple:
        """
        Run Qwen Code with a specific prompt.

        Args:
            prompt: The prompt to give to Qwen Code
            timeout: Maximum seconds to wait

        Returns:
            tuple: (success: bool, output: str)
        """
        self.logger.log(f"Running Qwen Code: {prompt[:100]}...")

        try:
            # Try to find qwen executable
            qwen_path = 'qwen'
            
            # Try npm global path on Windows
            npm_path = Path(os.environ.get('APPDATA', '')) / 'npm' / 'qwen.cmd'
            if npm_path.exists():
                qwen_path = str(npm_path)
                self.logger.log(f"Using qwen at: {qwen_path}")
            
            # Build command
            cmd = [qwen_path, '-p', prompt, '-y']

            # Set UTF-8 environment
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'

            # Run Qwen Code
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=str(self.vault_path),
                env=env
            )

            output = result.stdout

            if result.returncode == 0:
                self.logger.log("Qwen Code completed successfully")
                return True, output
            else:
                self.logger.log_error(f"Qwen Code failed: {result.stderr}")
                return False, result.stderr

        except subprocess.TimeoutExpired:
            self.logger.log_error(f"Qwen Code timed out after {timeout}s")
            return False, ""
        except FileNotFoundError:
            self.logger.log_error("Qwen Code not found in PATH")
            return False, ""
        except Exception as e:
            self.logger.log_error(f"Qwen Code error: {e}")
            return False, ""
    
    def send_email_via_mcp(self, filepath: Path) -> bool:
        """
        Send email from approved file by calling send_email.py directly.
        
        Args:
            filepath: Path to approved email file
            
        Returns:
            bool: True if successful
        """
        self.logger.log(f"Sending email from approved file: {filepath.name}")
        
        try:
            # Use send_email.py script
            script_path = Path(__file__).parent / '.qwen' / 'skills' / 'gmail-sender' / 'scripts' / 'send_email.py'
            
            if not script_path.exists():
                # Try alternate path
                script_path = Path(__file__).parents[1] / '.qwen' / 'skills' / 'gmail-sender' / 'scripts' / 'send_email.py'
            
            if script_path.exists():
                # Run send_email.py for the specific file
                cmd = [
                    'python', str(script_path), 
                    str(self.vault_path), 
                    '--action', 'send',
                    '--file', filepath.name
                ]
                
                # Set UTF-8 environment to prevent encoding errors
                env = os.environ.copy()
                env['PYTHONIOENCODING'] = 'utf-8'
                
                result = subprocess.run(
                    cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=120,
                    env=env
                )
                
                # Check both return code AND output for success confirmation
                output = result.stdout + result.stderr
                success_indicators = [
                    'Email sent successfully',
                    '✓ Email sent',
                    'sent successfully',
                    'Message ID:',
                    'Success: 1',
                    'success: 1'
                ]
                
                is_success = result.returncode == 0 and any(
                    indicator.lower() in output.lower() 
                    for indicator in success_indicators
                )
                
                if is_success:
                    self.logger.log(f"Email sent successfully: {filepath.name}")
                    return True
                else:
                    self.logger.log_error(
                        f"Email send failed for {filepath.name}\n"
                        f"Return code: {result.returncode}\n"
                        f"Stdout: {result.stdout}\n"
                        f"Stderr: {result.stderr}"
                    )
                    return False
            else:
                self.logger.log_error("send_email.py not found")
                return False
                
        except Exception as e:
            self.logger.log_error(f"Email send error: {e}")
            return False
    
    def move_to_done(self, filepath: Path):
        """Move a file to Done folder (only if not already moved by the script)."""
        try:
            if not filepath.exists():
                self.logger.log(f"File already moved (by send script): {filepath.name}")
                return
            dest = self.done / filepath.name
            shutil.move(str(filepath), str(dest))
            self.logger.log(f"Moved to Done: {filepath.name}")
        except Exception as e:
            self.logger.log_error(f"Move to Done failed: {e}")
    
    def process_needs_action(self, filepath: Path):
        """Process a new file in Needs_Action by having Qwen generate reply text, then creating the draft file ourselves."""
        if filepath.name in self.processed_files:
            return

        self.processed_files.add(filepath.name)
        self.logger.log(f"Processing Needs_Action: {filepath.name}")

        # Read the file content
        try:
            file_content = filepath.read_text(encoding='utf-8')
        except:
            file_content = "(unable to read file)"

        # Extract metadata from frontmatter
        import re
        to_match = re.search(r'from:\s*(.+)', file_content)
        subject_match = re.search(r'subject:\s*(.+)', file_content)
        
        sender_email = to_match.group(1).strip() if to_match else "unknown@example.com"
        original_subject = subject_match.group(1).strip() if subject_match else "No Subject"
        reply_subject = f"Re: {original_subject}" if not original_subject.startswith("Re:") else original_subject

        # Ask Qwen to generate reply text only
        prompt = f"""Generate a professional email reply to this incoming email. Output ONLY the reply text - no markdown, no explanations, no file creation.

Original email:
{file_content}

Reply guidelines:
- Professional and courteous
- Address the sender's question/request directly
- Keep it concise (3-4 paragraphs max)
- End with "Best regards,\\nAI Employee"

Output ONLY the reply text, nothing else."""

        success, qwen_output = self.run_qwen_code(prompt)

        if success and qwen_output.strip():
            self.logger.log("Qwen generated reply text")
            reply_body = qwen_output.strip()
        else:
            # Fallback: Generate a simple default reply if Qwen fails
            self.logger.log("Using fallback reply (Qwen unavailable)")
            reply_body = f"""Thank you for your email regarding "{original_subject}".

I have received your message and will review it shortly. I appreciate your patience and will respond with a detailed reply soon.

Best regards,
AI Employee"""
        
        # Create the draft file ourselves
        import re as re_mod
        safe_filename = re_mod.sub(r'[^a-zA-Z0-9_\-\.]', '_', filepath.name.replace('EMAIL_', ''))
        draft_filename = f"EMAIL_REPLY_{safe_filename}"
        draft_path = self.pending_approval / draft_filename
        
        # Build the draft content
        timestamp = datetime.now().isoformat()
        draft_content = f"""---
type: email_draft
to: {sender_email}
subject: {reply_subject}
created: {timestamp}
status: pending_approval
---

## Draft Content

{reply_body}

---

## Actions
- [ ] Review and edit if needed
- [ ] Approve and send by moving to Approved/ folder
"""
        
        # Write the draft file
        try:
            draft_path.write_text(draft_content, encoding='utf-8')
            self.logger.log(f"[OK] Draft created in Pending_Approval/: {draft_filename}")
            
            # Move original file to Done (Silver Tier requirement)
            try:
                done_path = self.done / filepath.name
                filepath.rename(done_path)
                self.logger.log(f"[OK] Original file moved to Done/: {filepath.name}")
            except Exception as e:
                self.logger.log_error(f"Failed to move original file to Done/: {e}")
        except Exception as e:
            self.logger.log_error(f"Failed to create draft file: {e}")
    
    def process_approved(self, filepath: Path):
        """Process a file in Approved folder."""
        if filepath.name in self.processed_files:
            return
        
        self.processed_files.add(filepath.name)
        self.logger.log(f"Processing Approved: {filepath.name}")
        
        # Determine action type based on filename or content
        action_type = self._detect_action_type(filepath)
        
        if action_type == 'email':
            # Send email via MCP/script
            success = self.send_email_via_mcp(filepath)
            if success:
                self.move_to_done(filepath)
            else:
                self.logger.log_error(f"Email send failed, file remains in Approved: {filepath.name}")
                
        elif action_type == 'linkedin':
            # Post to LinkedIn
            success = self.post_to_linkedin(filepath)
            if success:
                self.move_to_done(filepath)
            else:
                self.logger.log_error(f"LinkedIn post failed, file remains in Approved: {filepath.name}")
        
        else:
            # Other approved action - just move to Done
            self.logger.log(f"Approved action completed: {filepath.name}")
            self.move_to_done(filepath)
    
    def _detect_action_type(self, filepath: Path) -> str:
        """Detect what type of action this approved file requires."""
        name_upper = filepath.name.upper()
        
        # Check filename for keywords
        if 'EMAIL' in name_upper or name_upper.startswith('EMAIL_'):
            return 'email'
        
        if 'LINKEDIN' in name_upper or 'LINKEDIN_POST' in name_upper:
            return 'linkedin'
        
        # Check file content for type metadata
        try:
            content = filepath.read_text(encoding='utf-8')
            if 'type: email' in content or 'type:email_draft' in content:
                return 'email'
            if 'type: linkedin_post' in content or 'type:linkedin_post' in content:
                return 'linkedin'
        except:
            pass
        
        return 'unknown'
    
    def post_to_linkedin(self, filepath: Path) -> bool:
        """
        Post to LinkedIn using the linkedin-poster script.
        
        Args:
            filepath: Path to approved LinkedIn post file
            
        Returns:
            bool: True if successful
        """
        self.logger.log(f"Posting to LinkedIn from approved file: {filepath.name}")
        
        try:
            # Find the LinkedIn poster script
            script_path = Path(__file__).parent / '.qwen' / 'skills' / 'linkedin-poster' / 'scripts' / 'post_linkedin.py'
            
            if not script_path.exists():
                # Try alternate path (project root)
                script_path = Path(__file__).parents[0] / '.qwen' / 'skills' / 'linkedin-poster' / 'scripts' / 'post_linkedin.py'
            
            if script_path.exists():
                # Use the draft-and-post action to post this specific file
                # First, we need to read the content and post it
                cmd = [
                    'python', str(script_path),
                    str(self.vault_path),
                    '--action', 'post'
                ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0 and 'Success: 1' in result.stdout:
                    self.logger.log(f"LinkedIn post successful: {filepath.name}")
                    return True
                else:
                    self.logger.log_error(f"LinkedIn post failed: {result.stderr}")
                    return False
            else:
                self.logger.log_error("post_linkedin.py not found")
                return False
                
        except Exception as e:
            self.logger.log_error(f"LinkedIn post error: {e}")
            return False
    
    def process_rejected(self, filepath: Path):
        """Process a file in Rejected folder."""
        if filepath.name in self.processed_files:
            return
        
        self.processed_files.add(filepath.name)
        self.logger.log(f"Processing Rejected: {filepath.name}")
        
        # Log rejection and move to Done
        self.logger.log(f"Rejected: {filepath.name} - discarded")
        self.move_to_done(filepath)
    
    def setup_watchers(self):
        """Setup folder watchers using watchdog."""
        self.logger.log("Setting up folder watchers...")
        
        observer = Observer()
        
        # Watch Needs_Action
        na_handler = FolderHandler('Needs_Action', self)
        observer.schedule(na_handler, str(self.needs_action), recursive=False)
        self.logger.log(f"Watching: {self.needs_action}")
        
        # Watch Approved
        ap_handler = FolderHandler('Approved', self)
        observer.schedule(ap_handler, str(self.approved), recursive=False)
        self.logger.log(f"Watching: {self.approved}")
        
        # Watch Rejected
        rej_handler = FolderHandler('Rejected', self)
        observer.schedule(rej_handler, str(self.rejected), recursive=False)
        self.logger.log(f"Watching: {self.rejected}")
        
        observer.start()
        self.logger.log("All watchers started")
        
        return observer
    
    def setup_schedule(self):
        """Setup scheduled tasks."""
        self.logger.log("Setting up scheduled tasks...")
        
        # Every 3 minutes - check Needs_Action
        schedule.every(3).minutes.do(self.check_needs_action)
        self.logger.log("Scheduled: Check Needs_Action every 3 minutes")
        
        # LinkedIn post generation - 10:00 AM, 11:00 PM, 11:15 PM
        schedule.every().day.at("10:00").do(self.trigger_linkedin_post)
        schedule.every().day.at("23:00").do(self.trigger_linkedin_post)
        schedule.every().day.at("23:15").do(self.trigger_linkedin_post)
        
        # TEST: LinkedIn trigger at 17:37 (remove after testing)
        schedule.every().day.at("17:47").do(self.trigger_linkedin_post)
        
        self.logger.log("Scheduled: LinkedIn posts at 10:00, 23:00, 23:15 (+ TEST: 17:37)")
        
        # Business Audit - Sunday 9:00 PM
        schedule.every().sunday.at("21:00").do(self.trigger_business_audit)
        self.logger.log("Scheduled: Business audit every Sunday at 21:00")
    
    def check_needs_action(self):
        """Periodically check Needs_Action for new files."""
        self.logger.log("Scheduled check: Needs_Action")
        
        files = list(self.needs_action.glob('*.md'))
        if files:
            self.logger.log(f"Found {len(files)} file(s) in Needs_Action")
            for f in files:
                if f.name not in self.processed_files:
                    self.process_needs_action(f)
        else:
            self.logger.log("No files in Needs_Action")
    
    def trigger_linkedin_post(self):
        """Trigger LinkedIn post generation."""
        self.logger.log("Scheduled: LinkedIn post generation")
        
        # Generate timestamp and filename
        timestamp = datetime.now().strftime('%Y-%m-%d')
        safe_day = datetime.now().strftime('%A')
        safe_filename = f"LinkedIn_Post_{safe_day}_{timestamp}.md"
        
        # Ask Qwen to generate only the post text
        prompt = (
            f"Create a professional LinkedIn post on ONE of these rotating topics based on today's day ({safe_day}): "
            f"Monday: AI and automation trends. "
            f"Tuesday: Python programming tips. "
            f"Wednesday: Freelancing and productivity. "
            f"Thursday: Software development best practices. "
            f"Friday: Weekly business wins and lessons learned. "
            f"Saturday: Tech tools and resources worth sharing. "
            f"Sunday: Motivation and mindset for the week ahead. "
            f"\n\n"
            f"Output ONLY the LinkedIn post text - no explanations, no markdown code blocks, no file creation. "
            f"Write an engaging, professional post with relevant hashtags (150-300 words, 3-5 hashtags)."
        )

        success, qwen_output = self.run_qwen_code(prompt)
        
        if success and qwen_output.strip():
            self.logger.log("Qwen generated LinkedIn post text")
            post_content = qwen_output.strip()
        else:
            # Fallback: Generate a default post
            self.logger.log("Using fallback LinkedIn post (Qwen unavailable)")
            post_content = f"""🚀 {safe_day} Tech Insights!

Today I'm thinking about the future of AI and automation. The landscape is evolving rapidly, and it's exciting to see what's coming next.

Key trends I'm watching:
1️⃣ Autonomous AI agents becoming mainstream
2️⃣ Low-code/no-code tools democratizing development
3️⃣ AI-powered development assistants like Claude Code

What trends are you most excited about?

#AI #Automation #TechTrends #Innovation #{safe_day.replace(' ', '')}Thoughts"""
        
        # Create the LinkedIn post file ourselves
        draft_path = self.pending_approval / safe_filename
        
        # Build the file content
        file_content = f"""---
type: linkedin_post
topic: {safe_day} Tech Insights
created: {datetime.now().isoformat()}
status: draft
---

{post_content}
"""
        
        # Write the draft file
        try:
            draft_path.write_text(file_content, encoding='utf-8')
            self.logger.log(f"[OK] LinkedIn post draft created in Pending_Approval/: {safe_filename}")
            # Auto-approve: move to Approved
            approved_path = self.approved / safe_filename
            draft_path.rename(approved_path)
            self.logger.log(f"[OK] LinkedIn post auto-approved and moved to Approved/")
            
            # Move original from Needs_Action to Done (Silver Tier requirement)
            # Check we have a matching file in Needs_Action that was processed
            if filepath.name in self.processed_files:
                # For now, just move the original file to Done
                try:
                    # Create a simple Done file with the same base name
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    done_file = self.done / f"LINKEDIN_DONE_{timestamp}_{filepath.name.split('_')[1]}.md"
                    done_file.write_text(f"""Processed LinkedIn post draft created.
Original file: {filepath.name}
Post content: {post_content[:100]}...
""")
                    self.logger.log(f"[OK] Original file moved to Done/ folder")
                except Exception as e:
                    self.logger.log_error(f"Failed to move original file to Done/: {e}")
        except Exception as e:
            self.logger.log_error(f"Failed to create LinkedIn post file: {e}")
    
    def trigger_business_audit(self):
        """Trigger weekly business audit."""
        self.logger.log("Scheduled: Business audit")
        
        prompt = (
            "Perform a weekly business audit. "
            "Read Business_Goals.md to check progress. "
            "Review completed tasks in Done/ folder. "
            "Generate a CEO Briefing in Briefings/ folder. "
            "Include revenue, bottlenecks, and proactive suggestions."
        )
        
        self.run_qwen_code(prompt)
    
    def run(self):
        """Main orchestrator loop."""
        self.logger.log("Starting orchestrator main loop...")
        
        # Setup watchers
        observer = self.setup_watchers()
        
        # Setup schedule
        self.setup_schedule()
        
        # Initial check
        self.check_needs_action()
        
        # Main loop
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.log("Orchestrator stopping...")
            observer.stop()
        finally:
            observer.join()
            self.logger.log("Orchestrator stopped")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='AI Employee Orchestrator')
    parser.add_argument('--vault-path', type=str, default='AI_Employee_Vault',
                       help='Path to Obsidian vault (default: AI_Employee_Vault)')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path).resolve()
    
    if not vault_path.exists():
        print(f"Error: Vault path not found: {vault_path}")
        sys.exit(1)
    
    orchestrator = Orchestrator(vault_path)
    orchestrator.run()


if __name__ == "__main__":
    main()
