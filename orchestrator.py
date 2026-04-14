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
    
    def run_qwen_code(self, prompt: str, timeout: int = 300) -> bool:
        """
        Run Qwen Code with a specific prompt.
        
        Args:
            prompt: The prompt to give to Qwen Code
            timeout: Maximum seconds to wait
            
        Returns:
            bool: True if successful
        """
        self.logger.log(f"Running Qwen Code: {prompt[:100]}...")
        
        try:
            # Build command
            cmd = ['qwen', '-p', prompt, '-y']
            
            # Run Qwen Code
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=timeout,
                cwd=str(self.vault_path),
                shell=True          # Required on Windows to resolve PATH-based commands
            )
            
            if result.returncode == 0:
                self.logger.log("Qwen Code completed successfully")
                return True
            else:
                self.logger.log_error(f"Qwen Code failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            self.logger.log_error(f"Qwen Code timed out after {timeout}s")
            return False
        except FileNotFoundError:
            self.logger.log_error("Qwen Code not found in PATH")
            return False
        except Exception as e:
            self.logger.log_error(f"Qwen Code error: {e}")
            return False
    
    def send_email_via_mcp(self, filepath: Path) -> bool:
        """
        Send email using the email MCP server or send_email.py script.
        
        Args:
            filepath: Path to approved email file
            
        Returns:
            bool: True if successful
        """
        self.logger.log(f"Sending email from approved file: {filepath.name}")
        
        try:
            # Use send_email.py script as MCP server may not be running
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
                
                # Check both return code AND output for success
                output = result.stdout + result.stderr
                success_indicators = [
                    'Email sent successfully',
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
            self.logger.log_error(f"Email MCP error: {e}")
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
        """Process a new file in Needs_Action."""
        if filepath.name in self.processed_files:
            return
        
        self.processed_files.add(filepath.name)
        self.logger.log(f"Processing Needs_Action: {filepath.name}")
        
        # Trigger Qwen Code to process the file
        prompt = (
            f"Read the file 'Needs_Action/{filepath.name}'. "
            f"Check the 'type' field in the frontmatter to understand what kind of action it is "
            f"(email, whatsapp, linkedin, task, etc.). "
            f"Based on the type, draft an appropriate response or action plan. "
            f"Save the draft to Pending_Approval/ with relevant frontmatter fields "
            f"(e.g. 'to:' for emails, 'phone:' for WhatsApp, etc.). "
            f"if it is simple task, complete it and move it to done"
            f"follow the Company_Handbook.md  for rules and guidelines"
        )
        
        success = self.run_qwen_code(prompt)
        
        if success:
            self.logger.log(f"Processed successfully: {filepath.name}")
        else:
            self.logger.log_error(f"Processing failed: {filepath.name}")
    
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
        
        # TEST: LinkedIn trigger at 00:51 (remove after testing)
        schedule.every().day.at("00:51").do(self.trigger_linkedin_post)
        
        self.logger.log("Scheduled: LinkedIn posts at 10:00, 23:00, 23:15 (+ TEST: 00:51)")
        
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
        
        prompt = (
            # Old generic prompt (kept for reference):
            # "Create a LinkedIn post draft about recent business activities. "
            # "Check the Done/ folder for completed tasks to generate content. "
            # "Save the draft to Pending_Approval/."

            f"Create a professional LinkedIn post on ONE of these rotating topics based on today's day: "
            f"Monday: AI and automation trends. "
            f"Tuesday: Python programming tips. "
            f"Wednesday: Freelancing and productivity. "
            f"Thursday: Software development best practices. "
            f"Friday: Weekly business wins and lessons learned. "
            f"Saturday: Tech tools and resources worth sharing. "
            f"Sunday: Motivation and mindset for the week ahead. "
            f"Today is {datetime.now().strftime('%A')}. "
            f"Write an engaging, professional post with relevant hashtags. "
            f"Save the draft to AI_Employee_Vault/Pending_Approval/ and wait for human approval."
        )
        
        self.run_qwen_code(prompt)
    
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
