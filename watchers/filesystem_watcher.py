#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File System Watcher - Monitors a drop folder for new files.

This is the Bronze Tier Watcher - simplest to set up and test.
When a file is dropped into the Inbox folder, this watcher:
1. Detects the new file
2. Creates a corresponding .md action file in Needs_Action
3. Copies the original file for processing

Usage:
    python filesystem_watcher.py /path/to/AI_Employee_Vault
"""

import sys
import shutil
import logging
import time
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

from base_watcher import BaseWatcher


class DropFolderHandler(FileSystemEventHandler, BaseWatcher):
    """
    Watches a drop folder and creates action files for new files.

    Combines FileSystemEventHandler (for watchdog) with BaseWatcher
    to create a complete file monitoring solution.
    """

    # Prefix for watcher-generated files (to identify and skip them)
    GENERATED_FILE_PREFIX = 'FILE_'

    def __init__(self, vault_path: str):
        """
        Initialize the File System Watcher.

        Args:
            vault_path: Path to the Obsidian vault root
        """
        # Initialize BaseWatcher with 30-second check interval
        BaseWatcher.__init__(self, vault_path, check_interval=30)

        # Setup drop folder (Inbox)
        self.drop_folder = self.vault_path / 'Inbox'
        self.drop_folder.mkdir(parents=True, exist_ok=True)

        # Track files currently being processed (to avoid infinite loops)
        self.processing_files = set()

        self.logger.info(f'Drop folder: {self.drop_folder}')
        self.logger.info(f'Watching ONLY: {self.drop_folder}')
        self.logger.info(f'Generated files prefix: {self.GENERATED_FILE_PREFIX}')
    
    def on_created(self, event):
        """
        Handle file creation events.

        CRITICAL: Only process user-dropped files in /Inbox.
        Ignore any files created by the watcher itself to prevent infinite loops.

        Args:
            event: FileSystemEvent object
        """
        if event.is_directory:
            return

        source_path = Path(event.src_path)

        # STRICT CHECK: Only process files directly in /Inbox (not subdirectories)
        # This prevents processing files created in /Needs_Action or anywhere else
        if source_path.parent != self.drop_folder:
            self.logger.debug(f'Ignoring file outside Inbox: {source_path}')
            return

        # SAFETY 1: Skip watcher-generated files (files starting with FILE_)
        # These are created by the watcher in Needs_Action
        if source_path.name.startswith(self.GENERATED_FILE_PREFIX):
            self.logger.debug(f'Ignoring watcher-generated file: {source_path.name}')
            return

        # SAFETY 2: Skip temporary files (e.g., ~$ files from Office)
        if source_path.name.startswith('~$'):
            self.logger.debug(f'Ignoring temporary file: {source_path.name}')
            return

        # SAFETY 3: Skip files currently being processed (prevents race conditions)
        file_key = str(source_path.resolve())
        if file_key in self.processing_files:
            self.logger.debug(f'File already being processed: {source_path.name}')
            return

        self.logger.info(f'New file detected: {source_path.name}')

        try:
            self.process_file(source_path)
        except Exception as e:
            self.logger.error(f'Error processing file {source_path.name}: {e}')
    
    def process_file(self, source: Path):
        """
        Process a new file: copy to Needs_Action and create metadata.
        
        IMPORTANT: Does NOT create files in Inbox to avoid infinite loops.
        All output goes to Needs_Action folder only.

        Args:
            source: Path to the source file
        """
        # Add to processing set to prevent re-triggering
        file_key = str(source.resolve())
        self.processing_files.add(file_key)

        try:
            # Create unique filename
            safe_name = self.sanitize_filename(source.name)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            dest_name = f'FILE_{timestamp}_{safe_name}'
            dest = self.needs_action / dest_name

            # Copy the file to Needs_Action
            shutil.copy2(source, dest)
            self.logger.info(f'Copied file to: {dest.name}')

            # Read text content if possible
            text_content = self.read_text_content(source)

            # Create metadata file in Needs_Action (NOT in Inbox)
            self.create_metadata(source, dest, text_content)

            # Delete the original file from Inbox
            source.unlink()
            self.logger.info(f'Deleted original file: {source.name}')
        finally:
            # Remove from processing set when done
            self.processing_files.discard(file_key)
            self.logger.debug(f'Removed from processing set: {source.name}')
    
    def read_text_content(self, source: Path) -> str:
        """Try to read text content from a file."""
        text_extensions = {'.txt', '.md', '.csv', '.json', '.xml', '.html', '.log', '.py', '.js'}
        if source.suffix.lower() in text_extensions:
            try:
                return source.read_text(encoding='utf-8', errors='replace')
            except Exception:
                pass
        return ''

    def create_metadata(self, source: Path, dest: Path, text_content: str = ''):
        """
        Create a Markdown metadata file for the dropped file in Needs_Action.
        
        Args:
            source: Path to the original file
            dest: Path to the copied file
            text_content: Text content of the file (if readable)
        """
        meta_path = dest.with_suffix('.md')
        
        # Get file info
        file_size = source.stat().st_size
        file_type = source.suffix.lower().replace('.', '')

        content_section = ''
        if text_content:
            content_section = f'\n## 📄 File Content\n\n```\n{text_content}\n```\n'
        
        content = f'''---
type: file_drop
original_name: {source.name}
copied_to: {dest.name}
size: {file_size}
file_type: {file_type}
received: {self.get_timestamp()}
status: pending
---

# File Dropped for Processing

## File Information
- **Original Name:** {source.name}
- **File Type:** {file_type.upper()}
- **Size:** {self.format_size(file_size)}
- **Received:** {self.get_timestamp()}
{content_section}
## Suggested Actions
- [ ] Review file contents
- [ ] Process and extract relevant information
- [ ] Take appropriate action
- [ ] Move to /Done when complete

## Notes
<!-- Add your notes here -->

'''
        meta_path.write_text(content, encoding='utf-8')
        self.logger.info(f'Created metadata: {meta_path.name}')
    
    def format_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format.
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} TB"
    
    # BaseWatcher abstract method implementations
    
    def check_for_updates(self) -> list:
        """
        Check for new files in the drop folder.
        
        Note: This method is not used when running as event-driven
        (watchdog handles events), but required by BaseWatcher.
        
        Returns:
            Empty list (we use event-driven approach)
        """
        return []
    
    def create_action_file(self, item) -> Path:
        """
        Create action file for an item.
        
        Note: Not used in event-driven approach, but required by BaseWatcher.
        
        Args:
            item: Item to process
            
        Returns:
            None
        """
        return None




def main():
    """Main entry point for running the File System Watcher."""
    if len(sys.argv) < 2:
        print("Usage: python filesystem_watcher.py <vault_path>")
        print("Example: python filesystem_watcher.py ./AI_Employee_Vault")
        sys.exit(1)
    
    vault_path = sys.argv[1]
    
    # Validate vault path
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Create handler and observer
    handler = DropFolderHandler(vault_path)
    observer = Observer()
    observer.schedule(handler, str(handler.drop_folder), recursive=False)
    
    # Start watching
    observer.start()
    handler.logger.info('File System Watcher started')
    handler.logger.info(f'Watching folder: {handler.drop_folder}')
    handler.logger.info('Drop files into the Inbox folder to trigger processing')
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        handler.logger.info('File System Watcher stopped')
    
    observer.join()


if __name__ == "__main__":
    main()
