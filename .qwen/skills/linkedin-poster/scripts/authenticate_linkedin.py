#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Authentication Helper

This script helps you authenticate with LinkedIn by opening a browser
for manual login. Your session is saved for future automated posting.

Usage:
    python authenticate_linkedin.py [--email EMAIL] [--password PASSWORD]
"""

import sys
import os
import time
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
except ImportError:
    print("Missing dependency. Install with:")
    print("  pip install playwright")
    print("  playwright install chromium")
    sys.exit(1)


def authenticate_linkedin(email: str = None, password: str = None, 
                          session_path: str = '.linkedin_session'):
    """
    Authenticate with LinkedIn and save session.
    
    Args:
        email: LinkedIn email (optional - will prompt for manual login if not provided)
        password: LinkedIn password (optional)
        session_path: Path to save browser session data
    
    Returns:
        bool: True if authentication successful
    """
    session_path = Path(session_path)
    
    print("\n" + "="*60)
    print("LINKEDIN AUTHENTICATION")
    print("="*60)
    
    try:
        playwright = sync_playwright().start()
        
        # Launch browser with persistent context (saves session)
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=False,  # Must be visible for manual login
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.set_viewport_size({'width': 1280, 'height': 720})
        
        # Navigate to LinkedIn login
        print("\nOpening LinkedIn login page...")
        page.goto('https://www.linkedin.com/login', wait_until='networkidle')
        
        # Check if already logged in
        if 'feed' in page.url:
            print("\n✓ Already logged in to LinkedIn!")
            print(f"  Current URL: {page.url}")
            print("\nSession saved to:", session_path.absolute())
            context.close()
            return True
        
        # If credentials provided, try automated login
        if email and password:
            print("\nAttempting automated login...")
            
            try:
                # Find and fill email field
                email_field = page.locator('input[id="username"]')
                email_field.fill(email)
                
                # Find and fill password field
                password_field = page.locator('input[id="password"]')
                password_field.fill(password)
                
                # Click sign in button
                sign_in_btn = page.locator('button[type="submit"]')
                sign_in_btn.click()
                
                # Wait for navigation to feed
                print("Waiting for login to complete...")
                page.wait_for_url('**/feed/**', timeout=15000)
                
                print("\n✓ Automated login successful!")
                print(f"  Logged in as: {email}")
                print("\nSession saved to:", session_path.absolute())
                context.close()
                return True
                
            except PlaywrightTimeout:
                print("\n⚠ Automated login failed. Falling back to manual login...")
                # Continue to manual login below
        
        # Manual login
        print("\n" + "="*60)
        print("MANUAL LOGIN REQUIRED")
        print("="*60)
        print("\nA browser window is now open.")
        print("Please log in to LinkedIn manually.")
        print("\nSteps:")
        print("  1. Enter your email and password")
        print("  2. Complete any CAPTCHA if shown")
        print("  3. Wait for your LinkedIn feed to load")
        print("\nOnce logged in, the script will detect it and save your session.")
        print("\nWaiting up to 120 seconds for login...")
        print("="*60)
        
        try:
            # Wait for user to login (detect feed URL)
            page.wait_for_url('**/feed/**', timeout=120000)
            
            # Give it a moment to fully load
            time.sleep(2)
            
            print("\n✓ Manual login detected!")
            print(f"  Current URL: {page.url}")
            print("\nSession saved to:", session_path.absolute())
            print("\n" + "="*60)
            print("AUTHENTICATION COMPLETE")
            print("="*60)
            print("\nYour LinkedIn session is now saved locally.")
            print("Future posts can be automated without manual login.")
            print("\nNext step:")
            print("  python post_linkedin.py <vault_path> --action post")
            print("\nNote: Keep this session file private!")
            print(f"  Location: {session_path.absolute()}")
            
            context.close()
            return True
            
        except PlaywrightTimeout:
            print("\n❌ Login timeout. Please try again.")
            print("\nTroubleshooting:")
            print("  1. Ensure you have a LinkedIn account")
            print("  2. Check your internet connection")
            print("  3. Try again and complete login within 2 minutes")
            context.close()
            return False
            
    except Exception as e:
        print(f"\n❌ Authentication failed: {e}")
        return False


def check_session(session_path: str = '.linkedin_session'):
    """
    Check if LinkedIn session is still valid.
    
    Args:
        session_path: Path to session data
    
    Returns:
        bool: True if session is valid
    """
    session_path = Path(session_path)
    
    if not session_path.exists():
        print("❌ No LinkedIn session found.")
        print("Run authentication first: python authenticate_linkedin.py")
        return False
    
    print("✓ LinkedIn session file found.")
    print(f"  Location: {session_path.absolute()}")
    
    # Test session by opening LinkedIn
    try:
        playwright = sync_playwright().start()
        
        context = playwright.chromium.launch_persistent_context(
            user_data_dir=str(session_path),
            headless=True,
            args=['--no-sandbox']
        )
        
        page = context.pages[0] if context.pages else context.new_page()
        page.goto('https://www.linkedin.com', wait_until='networkidle', timeout=10000)
        
        if 'feed' in page.url or 'mynetwork' in page.url:
            print("✓ Session is valid!")
            context.close()
            return True
        else:
            print("⚠ Session may be expired. Re-authenticate if posting fails.")
            context.close()
            return False
            
    except Exception as e:
        print(f"⚠ Could not verify session: {e}")
        print("Session file exists but couldn't test it.")
        return False


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Authenticate with LinkedIn',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Manual login (recommended for first time)
  python authenticate_linkedin.py
  
  # Automated login
  python authenticate_linkedin.py --email "you@example.com" --password "yourpassword"
  
  # Check existing session
  python authenticate_linkedin.py --check
        """
    )
    
    parser.add_argument('--email', '-e', type=str, help='LinkedIn email')
    parser.add_argument('--password', '-p', type=str, help='LinkedIn password')
    parser.add_argument('--session', '-s', type=str, default='.linkedin_session',
                       help='Path to save session (default: .linkedin_session)')
    parser.add_argument('--check', '-c', action='store_true',
                       help='Check if existing session is valid')
    
    args = parser.parse_args()
    
    if args.check:
        success = check_session(args.session)
    else:
        success = authenticate_linkedin(args.email, args.password, args.session)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
