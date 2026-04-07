#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gmail Watcher Authentication Helper

This script helps you authenticate with Gmail API for the first time.
It will open a browser window for you to grant permissions.

Usage:
    python authenticate.py
"""

import os
import sys
from pathlib import Path

try:
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# Gmail API scopes - includes send permission for full email functionality
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.compose'
]


def authenticate(credentials_path: str = None, token_path: str = 'token.json'):
    """
    Authenticate with Gmail API and save token.
    
    Args:
        credentials_path: Path to OAuth credentials JSON
        token_path: Path to save OAuth token
    """
    # Default to secrets/ folder if not specified
    if credentials_path is None:
        project_root = Path(__file__).parents[4]
        credentials_path = str(project_root / 'secrets' / 'credential.json')
    
    credentials_path = Path(credentials_path)
    token_path = Path(token_path)
    
    creds = None
    
    # Check if credentials file exists
    if not credentials_path.exists():
        print(f"❌ Error: Credentials file not found: {credentials_path}")
        print("\nPlease ensure credential.json is in the secrets/ folder.")
        print("You can download it from Google Cloud Console:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Select your project")
        print("  3. APIs & Services > Credentials")
        print("  4. Download OAuth 2.0 Client ID credentials")
        return False
    
    # Load existing token if available
    if token_path.exists():
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
            print(f"✓ Found existing token file: {token_path}")
        except Exception as e:
            print(f"Warning: Could not load existing token: {e}")
    
    # Refresh expired token
    if creds and creds.expired and creds.refresh_token:
        print("Refreshing expired token...")
        try:
            creds.refresh(Request())
            print("✓ Token refreshed successfully")
        except Exception as e:
            print(f"Failed to refresh token: {e}")
            creds = None
    
    # Need new authentication
    if not creds or not creds.valid:
        print("\n" + "="*60)
        print("GMAIL API AUTHENTICATION")
        print("="*60)
        print("\nThis will open a browser window for you to grant permissions.")
        print("Please sign in with your Google account and allow access.")
        print("\nPermissions requested:")
        print("  • Read your Gmail messages")
        print("  • Send emails on your behalf")
        print("  • Compose draft emails")
        print("\n" + "="*60)
        input("\nPress Enter to open browser...")
        
        try:
            # Create OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES
            )
            
            # Run local server for OAuth callback
            creds = flow.run_local_server(
                port=8080,
                open_browser=True,
                authorization_prompt_message='\nOpening browser... Please complete authentication.\n',
                success_message='Authentication successful! You can close this window.'
            )
            
            print("\n✓ Authentication successful!")
            
        except Exception as e:
            print(f"\n❌ Authentication failed: {e}")
            print("\nTroubleshooting:")
            print("  1. Ensure Gmail API is enabled in Google Cloud Console")
            print("  2. Check that OAuth consent screen is configured")
            print("  3. Verify credentials.json is valid")
            return False
    
    # Save token
    try:
        token_path.parent.mkdir(parents=True, exist_ok=True)
        with open(token_path, 'w') as token:
            token.write(creds.to_json())
        print(f"✓ Token saved to: {token_path.absolute()}")
        
        # Get user email for confirmation
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        print(f"\n✓ Authenticated as: {profile.get('emailAddress')}")
        
        print("\n" + "="*60)
        print("AUTHENTICATION COMPLETE")
        print("="*60)
        print("\nYou can now use the Gmail Watcher:")
        print("  python gmail_watcher.py <vault_path>")
        print("\nOr send emails:")
        print("  python send_email.py <vault_path> --action send")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save token: {e}")
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Authenticate with Gmail API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python authenticate.py
  python authenticate.py --credentials custom.json --token my_token.json
        """
    )
    
    parser.add_argument(
        '--credentials', '-c',
        default=None,
        help='Path to OAuth credentials JSON (default: secrets/credential.json)'
    )
    
    parser.add_argument(
        '--token', '-t',
        default='token.json',
        help='Path to save OAuth token (default: token.json)'
    )
    
    args = parser.parse_args()
    
    success = authenticate(args.credentials, args.token)
    sys.exit(0 if success else 1)
