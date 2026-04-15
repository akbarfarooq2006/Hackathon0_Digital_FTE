#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI Employee Vault Initializer
Run this script to automatically create the required folder structure.
"""

import os
from pathlib import Path

def init_project():
    project_root = Path(__file__).parent.resolve()
    vault_path = project_root / 'AI_Employee_Vault'
    
    # 📂 Core Project Folders
    core_folders = [
        project_root / 'data',
        project_root / 'secrets',
        project_root / 'watchers',
    ]
    
    # 📂 Vault Folders
    vault_folders = [
        vault_path / 'Needs_Action',
        vault_path / 'Pending_Approval',
        vault_path / 'Approved',
        vault_path / 'Done',
        vault_path / 'Rejected',
        vault_path / 'Plans',
        vault_path / 'Logs',
        vault_path / 'Briefings',
    ]

    print("\n" + "="*50)
    print("🚀 Initializing AI Employee Project Structure")
    print("="*50 + "\n")

    # Create everything
    for folder in core_folders + vault_folders:
        if not folder.exists():
            folder.mkdir(parents=True, exist_ok=True)
            print(f"✅ Created: {folder.relative_to(project_root)}")
        else:
            print(f"ℹ️  Exists:  {folder.relative_to(project_root)}")

    print("\n" + "="*50)
    print("✨ Initialization Complete!")
    print("Your project is ready to be configured.")
    print("="*50 + "\n")

if __name__ == "__main__":
    init_project()
