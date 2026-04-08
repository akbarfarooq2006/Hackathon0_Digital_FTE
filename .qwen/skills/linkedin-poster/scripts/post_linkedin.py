#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Poster - Create and post content to LinkedIn.

This script uses Playwright to automate LinkedIn posting for the AI Employee.
It supports drafting posts, reviewing, and posting after approval.

Usage:
    python post_linkedin.py <vault_path> --action <draft|post|list>
"""

import sys
import os
import logging
import argparse
import time
from pathlib import Path
from datetime import datetime

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


class LinkedInPoster:
    """
    LinkedIn automation using Playwright.
    """
    
    def __init__(self, vault_path: str, email: str = None, password: str = None):
        """
        Initialize LinkedIn Poster.

        Args:
            vault_path: Path to the Obsidian vault root
            email: LinkedIn email (or from .env)
            password: LinkedIn password (or from .env)
        """
        # Resolve to absolute path immediately
        self.vault_path = Path(vault_path).resolve()
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.approved = self.vault_path / 'Approved'
        self.done = self.vault_path / 'Done'
        self.briefings = self.vault_path / 'Briefings'

        # Ensure folders exist
        for folder in [self.pending_approval, self.approved, self.done, self.briefings]:
            folder.mkdir(parents=True, exist_ok=True)

        # Load credentials from .env if not provided
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')

        # Session path in /data/ directory (runtime state, not skill definition)
        # vault_path is AI_Employee_Vault/, so project root is parent
        project_root = self.vault_path.parent
        self.session_path = project_root / "data" / ".linkedin_session"

        self.browser = None
        self.context = None
        self.page = None
        self.logger = logging.getLogger('LinkedInPoster')
        
        # Log paths for debugging
        self.logger.debug(f"Vault path: {self.vault_path}")
        self.logger.debug(f"Approved folder: {self.approved}")

    def _initialize_browser(self):
        """Initialize Playwright browser."""
        try:
            playwright = sync_playwright().start()

            self.context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=False,  # Show browser for debugging
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox'
                ]
            )

            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            self.page.set_viewport_size({'width': 1280, 'height': 720})

            self.logger.info("Browser initialized")
            self.logger.info(f"Session path: {self.session_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def login(self):
        """
        Login to LinkedIn. Checks saved session first, only goes to /login if expired.

        Returns:
            bool: True if login successful
        """
        try:
            # Step 1: Try going to feed first (check if session is valid)
            self.logger.info("Checking if existing session is valid...")
            try:
                self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)
            except PlaywrightTimeout:
                self.logger.warning("Feed page timed out, trying login page...")

            # Check if we landed on feed (session valid)
            if '/feed' in self.page.url or '/mynetwork' in self.page.url or '/jobs' in self.page.url:
                self.logger.info(f"Session valid! Current page: {self.page.url}")
                return True

            # Step 2: If redirected to login, go to login page
            if '/login' not in self.page.url:
                self.logger.info("Session expired, navigating to login page...")
                try:
                    self.page.goto('https://www.linkedin.com/login', wait_until='domcontentloaded', timeout=60000)
                except PlaywrightTimeout:
                    self.logger.warning("Login page timed out, continuing anyway...")

            # Check if already on feed after redirect
            if '/feed' in self.page.url:
                self.logger.info("Already logged in")
                return True

            # Step 3: Try automated login if credentials provided
            if self.email and self.password:
                self.logger.info("Attempting automated login...")

                try:
                    # Find and fill email field
                    email_field = self.page.locator('input[id="username"]')
                    email_field.fill(self.email)

                    # Find and fill password field
                    password_field = self.page.locator('input[id="password"]')
                    password_field.fill(self.password)

                    # Click sign in button
                    sign_in_btn = self.page.locator('button[type="submit"]')
                    sign_in_btn.click()

                    # Wait for navigation to feed
                    try:
                        self.page.wait_for_url('**/feed/**', timeout=30000)
                        self.logger.info("Login successful")
                        return True
                    except PlaywrightTimeout:
                        self.logger.error("Login failed - check credentials")
                        return False
                except Exception as e:
                    self.logger.warning(f"Automated login failed: {e}")

            # Step 4: Fall back to manual login
            self.logger.warning("No credentials provided or automated login failed")
            self.logger.info("Please login manually in the browser window")

            # Wait for user to login
            try:
                self.page.wait_for_url('**/feed/**', timeout=120000)  # 2 min timeout
                self.logger.info("Manual login detected")
                return True
            except PlaywrightTimeout:
                self.logger.error("Manual login timeout")
                return False

        except Exception as e:
            self.logger.error(f"Login error: {e}")
            return False
    
    def create_post(self, content: str):
        """
        Create a LinkedIn post.
        
        Args:
            content: Post content text
            
        Returns:
            bool: True if post created successfully
        """
        try:
            # Navigate to feed
            self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            time.sleep(2)
            
            # Click on "Start a post"
            try:
                start_post = self.page.locator('button:has-text("Start a post")').first
                start_post.click()
                time.sleep(1)
            except:
                self.logger.error("Could not find 'Start a post' button")
                return False
            
            # Find the text area and fill content
            try:
                # LinkedIn uses a contenteditable div for the post editor
                text_area = self.page.locator('div[contenteditable="true"][role="textbox"]').first
                text_area.fill(content)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Could not fill post content: {e}")
                return False
            
            # Click Post button
            try:
                post_button = self.page.locator('button:has-text("Post")').first
                post_button.click()
                
                # Wait for post to be published
                time.sleep(3)
                
                self.logger.info("Post published successfully")
                return True
                
            except Exception as e:
                self.logger.error(f"Could not click Post button: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating post: {e}")
            return False
    
    def get_post_content_from_file(self, filepath: Path) -> str:
        """
        Extract post content from approval file.
        
        Args:
            filepath: Path to approval file
            
        Returns:
            str: Post content
        """
        content = filepath.read_text(encoding='utf-8')
        
        # Try to extract content between markdown sections
        lines = content.split('\n')
        post_lines = []
        in_post = False
        
        for line in lines:
            if line.startswith('## Post Content') or line.startswith('## Content'):
                in_post = True
                continue
            elif line.startswith('##') and in_post:
                break
            elif in_post:
                post_lines.append(line)
        
        if post_lines:
            return '\n'.join(post_lines).strip()
        
        # Fallback: return everything after frontmatter
        if '---' in content:
            parts = content.split('---', 2)
            if len(parts) > 2:
                return parts[2].strip()
        
        return content
    
    def process_approved_posts(self):
        """
        Process all approved post files and publish them.

        Returns:
            dict: Results summary
        """
        results = {
            'processed': 0,
            'success': 0,
            'failed': 0,
            'files': []
        }

        # Find all approved LinkedIn post files
        # Look for ANY .md files in Approved folder, then check if they're LinkedIn posts
        approved_files = []
        for filepath in self.approved.glob('*.md'):
            try:
                content = filepath.read_text(encoding='utf-8')
                # Check if it's a LinkedIn post (has type: linkedin_post in frontmatter)
                if 'type: linkedin_post' in content or 'type:linkedin_post' in content:
                    approved_files.append(filepath)
            except Exception:
                continue

        if not approved_files:
            self.logger.info("No approved LinkedIn posts to process")
            self.logger.info(f"Checked folder: {self.approved}")
            self.logger.info(f"Folder exists: {self.approved.exists()}")
            # List what IS in the folder for debugging
            try:
                all_files = list(self.approved.glob('*'))
                if all_files:
                    self.logger.info(f"Found {len(all_files)} files in Approved folder:")
                    for f in all_files:
                        self.logger.info(f"  - {f.name} (is_file: {f.is_file()})")
                        # Check content for LinkedIn type
                        if f.is_file() and f.suffix == '.md':
                            try:
                                content = f.read_text(encoding='utf-8')
                                has_linkedin_type = 'type: linkedin_post' in content or 'type:linkedin_post' in content
                                self.logger.info(f"    Contains 'type: linkedin_post': {has_linkedin_type}")
                            except Exception as e:
                                self.logger.info(f"    Could not read file: {e}")
                else:
                    self.logger.info("Approved folder is empty")
            except Exception as e:
                self.logger.error(f"Could not list Approved folder: {e}")
            return results
        
        self.logger.info(f"Found {len(approved_files)} approved posts")
        
        # Initialize browser
        if not self._initialize_browser():
            return results
        
        # Login
        if not self.login():
            self.logger.error("Login failed - cannot process posts")
            return results
        
        for filepath in approved_files:
            self.logger.info(f"Processing: {filepath.name}")
            results['processed'] += 1
            
            try:
                # Extract content
                content = self.get_post_content_from_file(filepath)
                
                # Post to LinkedIn
                if self.create_post(content):
                    results['success'] += 1
                    results['files'].append({'file': filepath.name, 'status': 'success'})
                    
                    # Move to Done
                    dest = self.done / filepath.name
                    filepath.rename(dest)
                    self.logger.info(f"Moved to Done: {dest.name}")
                    
                    # Log to briefings
                    self._log_to_briefings(filepath.name, content)
                    
                else:
                    results['failed'] += 1
                    results['files'].append({'file': filepath.name, 'status': 'failed'})
                    
            except Exception as e:
                self.logger.error(f"Error processing {filepath.name}: {e}")
                results['failed'] += 1
                results['files'].append({'file': filepath.name, 'status': 'error', 'error': str(e)})
        
        # Cleanup
        if self.context:
            self.context.close()
        
        return results
    
    def _log_to_briefings(self, filename: str, content: str):
        """Log posted content to Briefings folder."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_file = self.briefings / f'linkedin_post_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
        
        log_content = f'''---
type: linkedin_post_log
original_file: {filename}
posted: {timestamp}
status: published
---

# LinkedIn Post Log

## Posted
{timestamp}

## Content

{content}

## Status
Successfully published to LinkedIn
'''
        log_file.write_text(log_content, encoding='utf-8')
    
    def close(self):
        """Close browser."""
        if self.context:
            self.context.close()
            self.logger.info("Browser closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LinkedIn Poster for AI Employee')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--action', type=str, choices=['draft', 'post', 'list'],
                       default='list', help='Action to perform')
    parser.add_argument('--email', type=str, help='LinkedIn email')
    parser.add_argument('--password', type=str, help='LinkedIn password')
    parser.add_argument('--topic', type=str, help='Post topic (for draft action)')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    poster = LinkedInPoster(
        vault_path=args.vault_path,
        email=args.email,
        password=args.password
    )
    
    if args.action == 'list':
        # List pending and approved posts (flexible pattern matching)
        def find_linkedin_posts(folder):
            """Find all LinkedIn post files in a folder."""
            posts = []
            for filepath in folder.glob('*.md'):
                try:
                    content = filepath.read_text(encoding='utf-8')
                    if 'type: linkedin_post' in content or 'type:linkedin_post' in content:
                        posts.append(filepath)
                except Exception:
                    continue
            return posts
        
        pending = find_linkedin_posts(poster.pending_approval)
        approved = find_linkedin_posts(poster.approved)

        print(f"\nVault path: {poster.vault_path}")
        print(f"Pending Approval: {len(pending)}")
        for f in pending:
            print(f"  - {f.name}")

        print(f"\nApproved (ready to post): {len(approved)}")
        for f in approved:
            print(f"  - {f.name}")
        
        if not pending and not approved:
            print("\nNo LinkedIn posts found.")
            print("Create a post with: qwen \"Create a LinkedIn post about [topic]\"")
    
    elif args.action == 'draft':
        # Create a draft post
        if not args.topic:
            print("Error: --topic required for draft action")
            sys.exit(1)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'LINKEDIN_{timestamp}_{args.topic.replace(" ", "_")[:20]}.md'
        filepath = poster.pending_approval / filename
        
        content = f'''---
type: linkedin_post
topic: {args.topic}
status: draft
created: {datetime.now().isoformat()}
---

# LinkedIn Post Draft

## Topic
{args.topic}

## Post Content

[Draft your LinkedIn post content here]

## Hashtags
#AI #Automation #Technology

---
## Instructions
1. Review and edit the content above
2. Move this file to /Approved to post
3. Move to /Rejected to discard
'''
        filepath.write_text(content, encoding='utf-8')
        print(f"Draft created: {filepath}")
    
    elif args.action == 'post':
        # Post all approved content
        print("Processing approved LinkedIn posts...")
        results = poster.process_approved_posts()
        
        print(f"\n=== Results ===")
        print(f"Processed: {results['processed']}")
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        
        for file_result in results['files']:
            status_icon = '✅' if file_result['status'] == 'success' else '❌'
            print(f"  {status_icon} {file_result['file']}")
    
    poster.close()


if __name__ == "__main__":
    main()
