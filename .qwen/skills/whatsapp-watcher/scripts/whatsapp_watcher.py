#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WhatsApp Watcher - Monitor WhatsApp Web for new messages.

This watcher uses Playwright to automate WhatsApp Web and check for 
unread messages containing urgent keywords.

Usage:
    python whatsapp_watcher.py <vault_path> [--keywords KEYWORDS] [--interval SECONDS]
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

# Add parent directory to path for base_watcher
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'watchers'))

from base_watcher import BaseWatcher


class WhatsAppWatcher(BaseWatcher):
    """
    Watcher for WhatsApp Web that monitors for unread messages with keywords.
    """
    
    def __init__(self, vault_path: str, session_path: str, check_interval: int = 30, 
                 keywords: list = None):
        """
        Initialize the WhatsApp Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            session_path: Path to store browser session data
            check_interval: Seconds between checks (default: 30)
            keywords: List of keywords to flag as high priority
        """
        super().__init__(vault_path, check_interval)
        
        self.session_path = Path(session_path)
        self.session_path.mkdir(parents=True, exist_ok=True)
        
        self.keywords = keywords or ['urgent', 'asap', 'invoice', 'payment', 'help', 'emergency']
        self.processed_chats = set()
        self.browser = None
        self.page = None
        self.context = None
        
        # Load processed chats from cache
        self._load_processed_cache()
    
    def _load_processed_cache(self):
        """Load previously processed chat IDs from cache file."""
        cache_file = self.vault_path / '.whatsapp_cache.json'
        if cache_file.exists():
            try:
                import json
                with open(cache_file) as f:
                    data = json.load(f)
                    self.processed_chats = set(data.get('processed_chats', []))
            except:
                pass
    
    def _save_processed_cache(self):
        """Save processed chat IDs to cache file."""
        cache_file = self.vault_path / '.whatsapp_cache.json'
        try:
            import json
            # Keep only last 500 chats to prevent unbounded growth
            chats_list = list(self.processed_chats)[-500:]
            with open(cache_file, 'w') as f:
                json.dump({'processed_chats': chats_list}, f)
        except:
            pass
    
    def _initialize_browser(self):
        """Initialize Playwright browser with persistent context."""
        try:
            playwright = sync_playwright().start()
            
            # Launch browser with persistent context (saves session)
            self.context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.session_path),
                headless=True,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-dev-shm-usage'
                ]
            )
            
            self.page = self.context.pages[0] if self.context.pages else self.context.new_page()
            
            # Set viewport
            self.page.set_viewport_size({'width': 1280, 'height': 720})
            
            self.logger.info("Browser initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def _navigate_to_whatsapp(self):
        """Navigate to WhatsApp Web and wait for load."""
        try:
            self.page.goto('https://web.whatsapp.com', wait_until='networkidle')
            
            # Wait for chat list or QR code
            try:
                self.page.wait_for_selector('[data-testid="chat-list"]', timeout=10000)
                self.logger.info("WhatsApp Web loaded (already authenticated)")
                return True
            except PlaywrightTimeout:
                # Check for QR code (needs authentication)
                if self.page.query_selector('[data-testid="qr-code"]'):
                    self.logger.warning("QR code detected - please scan with WhatsApp mobile app")
                    self.logger.info("Waiting up to 60 seconds for authentication...")
                    
                    try:
                        self.page.wait_for_selector('[data-testid="chat-list"]', timeout=60000)
                        self.logger.info("Authentication successful!")
                        return True
                    except PlaywrightTimeout:
                        self.logger.error("Authentication timeout - please restart and scan QR code")
                        return False
                
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to navigate to WhatsApp: {e}")
            return False
    
    def _get_unread_chats(self):
        """
        Get list of chats with unread messages.
        
        Returns:
            List of dicts with chat info
        """
        try:
            unread_chats = []
            
            # Find all chat elements with unread indicator
            chat_elements = self.page.query_selector_all('[data-testid="chat-list"] > div')
            
            for chat_el in chat_elements:
                try:
                    # Get chat name
                    name_el = chat_el.query_selector('[data-testid="chat-cell-title"]')
                    if not name_el:
                        continue
                    
                    chat_name = name_el.inner_text().strip()
                    
                    # Get last message
                    msg_el = chat_el.query_selector('[data-testid="chat-cell-last-message"]')
                    last_message = msg_el.inner_text().strip() if msg_el else ""
                    
                    # Check for unread indicator
                    unread_badge = chat_el.query_selector('[data-testid="unread-count"]')
                    is_unread = unread_badge is not None
                    
                    # Check if message contains keywords
                    message_lower = last_message.lower()
                    matched_keywords = [kw for kw in self.keywords if kw.lower() in message_lower]
                    
                    # Only process if unread OR has keywords
                    if is_unread or matched_keywords:
                        # Get timestamp if available
                        time_el = chat_el.query_selector('[data-testid="chat-cell-time"]')
                        timestamp = time_el.inner_text().strip() if time_el else datetime.now().strftime("%H:%M")
                        
                        unread_chats.append({
                            'name': chat_name,
                            'last_message': last_message,
                            'timestamp': timestamp,
                            'is_unread': is_unread,
                            'matched_keywords': matched_keywords
                        })
                        
                except Exception as e:
                    self.logger.debug(f"Error processing chat: {e}")
                    continue
            
            return unread_chats
            
        except Exception as e:
            self.logger.error(f"Error getting unread chats: {e}")
            return []
    
    def check_for_updates(self) -> list:
        """
        Check for new unread messages with keywords.
        
        Returns:
            List of new chats to process
        """
        # Initialize browser if needed
        if not self.browser or not self.page:
            if not self._initialize_browser():
                return []
            
            if not self._navigate_to_whatsapp():
                return []
        
        try:
            # Refresh page to get latest messages
            self.page.reload(wait_until='networkidle')
            time.sleep(2)  # Wait for messages to load
            
            unread_chats = self._get_unread_chats()
            new_chats = []
            
            for chat in unread_chats:
                chat_key = f"{chat['name']}_{chat['timestamp']}"
                if chat_key not in self.processed_chats:
                    new_chats.append(chat)
            
            return new_chats
            
        except Exception as e:
            self.logger.error(f"Error checking WhatsApp: {e}")
            # Try to recover by reinitializing
            self.browser = None
            self.page = None
            return []
    
    def create_action_file(self, chat) -> Path:
        """
        Create a Markdown action file for a WhatsApp message.
        
        Args:
            chat: Chat info dict
            
        Returns:
            Path to created file
        """
        # Mark as processed
        chat_key = f"{chat['name']}_{chat['timestamp']}"
        self.processed_chats.add(chat_key)
        self._save_processed_cache()
        
        # Determine priority
        priority = 'high' if chat['matched_keywords'] else 'normal'
        
        # Create action file
        safe_name = self.sanitize_filename(chat['name'])[:30]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'WHATSAPP_{timestamp}_{safe_name}.md'
        filepath = self.needs_action / filename
        
        keywords_str = ', '.join(chat['matched_keywords']) if chat['matched_keywords'] else 'none'
        
        content = f'''---
type: whatsapp_message
from: {chat['name']}
chat: {chat['name']}
received: {self.get_timestamp()}
priority: {priority}
status: pending
keywords: {keywords_str}
---

# WhatsApp Message

## From
{chat['name']}

## Received
{chat['timestamp']}

## Message Content

{chat['last_message']}

## Matched Keywords
{keywords_str}

## Suggested Actions
- [ ] Reply to sender
- [ ] Take appropriate action
- [ ] Mark as read in WhatsApp
- [ ] Archive after processing

## Notes
<!-- Add your notes here -->
'''
        
        filepath.write_text(content, encoding='utf-8')
        self.logger.info(f'Created action file for WhatsApp message from: {chat["name"]}')
        
        return filepath
    
    def run(self):
        """
        Main run loop - continuously monitors WhatsApp Web.
        """
        self.logger.info(f'Starting WhatsApp Watcher')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Session path: {self.session_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        self.logger.info(f'Keywords: {", ".join(self.keywords)}')
        
        # Initialize browser
        if not self._initialize_browser():
            self.logger.error("Failed to initialize browser")
            return
        
        # Navigate to WhatsApp
        if not self._navigate_to_whatsapp():
            self.logger.error("Failed to load WhatsApp Web")
            self.logger.info("Please restart and scan QR code with WhatsApp mobile app")
            return
        
        self.logger.info("WhatsApp Watcher started - monitoring for messages...")
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing messages: {e}')
                    # Attempt recovery
                    self.browser = None
                    self.page = None
                    time.sleep(5)
                
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            self.logger.info('WhatsApp Watcher stopped by user')
        
        finally:
            # Cleanup
            if self.context:
                self.context.close()
    
    def close(self):
        """Close browser and cleanup."""
        if self.context:
            self.context.close()
            self.logger.info("Browser closed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='WhatsApp Watcher for AI Employee')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--interval', type=int, default=30,
                       help='Check interval in seconds (default: 30)')
    parser.add_argument('--keywords', type=str, default='urgent,asap,invoice,payment,help,emergency',
                       help='Comma-separated keywords for high priority')
    parser.add_argument('--session', type=str, default='./.whatsapp_session',
                       help='Path to store browser session')
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Parse keywords
    keywords = [k.strip() for k in args.keywords.split(',') if k.strip()]
    
    # Create watcher
    watcher = WhatsAppWatcher(
        vault_path=args.vault_path,
        session_path=args.session,
        check_interval=args.interval,
        keywords=keywords
    )
    
    try:
        watcher.run()
    finally:
        watcher.close()


if __name__ == "__main__":
    main()
