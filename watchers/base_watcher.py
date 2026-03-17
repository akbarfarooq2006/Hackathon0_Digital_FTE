#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Base Watcher - Abstract base class for all Watcher scripts.

Watchers are lightweight Python scripts that run continuously in the background,
monitoring various inputs (Gmail, WhatsApp, filesystem, etc.) and creating
actionable .md files for Claude Code to process.
"""

import time
import logging
from pathlib import Path
from abc import ABC, abstractmethod
from datetime import datetime


class BaseWatcher(ABC):
    """
    Abstract base class for all Watcher implementations.
    
    All Watchers must implement:
    - check_for_updates(): Return list of new items to process
    - create_action_file(item): Create .md file in Needs_Action folder
    """
    
    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize the Watcher.
        
        Args:
            vault_path: Path to the Obsidian vault root
            check_interval: Seconds between checks (default: 60)
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        
        # Ensure Needs_Action folder exists
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.setLevel(logging.INFO)
        
        # Track processed items to avoid duplicates
        self.processed_ids = set()
    
    @abstractmethod
    def check_for_updates(self) -> list:
        """
        Check for new items that need processing.
        
        Returns:
            List of new items to process
        """
        pass
    
    @abstractmethod
    def create_action_file(self, item) -> Path:
        """
        Create a Markdown action file in the Needs_Action folder.
        
        Args:
            item: The item to create an action file for
            
        Returns:
            Path to the created file
        """
        pass
    
    def run(self):
        """
        Main run loop - continuously monitors for updates.
        
        This method runs indefinitely until interrupted (Ctrl+C).
        """
        self.logger.info(f'Starting {self.__class__.__name__}')
        self.logger.info(f'Vault path: {self.vault_path}')
        self.logger.info(f'Check interval: {self.check_interval}s')
        
        try:
            while True:
                try:
                    items = self.check_for_updates()
                    for item in items:
                        filepath = self.create_action_file(item)
                        self.logger.info(f'Created action file: {filepath.name}')
                except Exception as e:
                    self.logger.error(f'Error processing updates: {e}')
                
                time.sleep(self.check_interval)
        except KeyboardInterrupt:
            self.logger.info(f'{self.__class__.__name__} stopped by user')
    
    def get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now().isoformat()
    
    def sanitize_filename(self, name: str) -> str:
        """
        Sanitize a string for use as a filename.
        
        Args:
            name: The original name
            
        Returns:
            Sanitized filename-safe string
        """
        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|？*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name.strip()
