#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Email MCP Server - Model Context Protocol server for Gmail.

Exposes email tools that AI agents (like Qwen Code) can call directly:
- email_send(to, subject, body) - Send email immediately
- email_draft(to, subject, body) - Save draft to Pending_Approval/
- email_list(max_results) - List recent emails

Usage:
    python email_mcp_server.py [--vault-path PATH]

This server communicates via stdio using JSON-RPC 2.0 (MCP protocol).
"""

import sys
import os
import json
import logging
import argparse
import base64
from pathlib import Path
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Setup logging to stderr (so it doesn't interfere with MCP stdio)
logging.basicConfig(
    stream=sys.stderr,
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('email-mcp-server')

# Import Gmail dependencies
try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    logger.error("Missing dependencies. Install with:")
    logger.error("  pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
    sys.exit(1)


# MCP Protocol Version
MCP_PROTOCOL_VERSION = "2024-11-05"


class EmailMCPServer:
    """MCP server for Gmail operations."""
    
    def __init__(self, vault_path: str = None):
        """Initialize the MCP server."""
        # Find project root and vault path
        if vault_path is None:
            # Default: go up from this script to project root
            project_root = Path(__file__).parents[4]
            vault_path = str(project_root / 'AI_Employee_Vault')
        
        self.vault_path = Path(vault_path)
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.briefings = self.vault_path / 'Briefings'
        
        # Ensure folders exist
        self.pending_approval.mkdir(parents=True, exist_ok=True)
        self.briefings.mkdir(parents=True, exist_ok=True)
        
        # Setup Gmail credentials
        project_root = self.vault_path.parent
        self.credentials_path = project_root / 'secrets' / 'credential.json'
        self.token_path = project_root / 'data' / 'gmail_token.json'
        
        self.gmail_service = None
        self.gmail_user = None
        
        # MCP request ID counter
        self.request_id = 0
        
        logger.info(f"Email MCP Server initialized")
        logger.info(f"Vault path: {self.vault_path}")
        logger.info(f"Credentials: {self.credentials_path}")
        logger.info(f"Token: {self.token_path}")
    
    def authenticate_gmail(self):
        """Authenticate with Gmail API."""
        if self.gmail_service:
            return True
        
        if not self.credentials_path.exists():
            logger.error(f"Credentials file not found: {self.credentials_path}")
            raise FileNotFoundError(f"Credentials file not found. Run authenticate.py first.")
        
        creds = None
        
        # Load token
        if self.token_path.exists():
            try:
                creds = Credentials.from_authorized_user_file(
                    str(self.token_path),
                    ['https://www.googleapis.com/auth/gmail.send',
                     'https://www.googleapis.com/auth/gmail.readonly']
                )
            except Exception as e:
                logger.warning(f"Failed to load token: {e}")
        
        # Refresh if expired
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(self.token_path, 'w') as f:
                    f.write(creds.to_json())
                logger.info("Token refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh token: {e}")
                creds = None
        
        if not creds or not creds.valid:
            raise Exception("Gmail authentication failed. Run authenticate.py first.")
        
        # Build service
        self.gmail_service = build('gmail', 'v1', credentials=creds)
        profile = self.gmail_service.users().getProfile(userId='me').execute()
        self.gmail_user = profile.get('emailAddress')
        
        logger.info(f"Gmail authenticated as: {self.gmail_user}")
        return True
    
    def _create_message(self, to: str, subject: str, body: str, 
                       cc: str = None, reply_to: str = None) -> dict:
        """Create a Gmail API message."""
        message = MIMEMultipart()
        message['to'] = to
        message['from'] = self.gmail_user
        message['subject'] = subject
        
        if cc:
            message['cc'] = cc
        if reply_to:
            message['In-Reply-To'] = reply_to
            message['References'] = reply_to
        
        message.attach(MIMEText(body, 'plain', 'utf-8'))
        
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}
    
    def email_send(self, to: str, subject: str, body: str, 
                   cc: str = None) -> dict:
        """
        Send an email via Gmail API.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (optional)
        
        Returns:
            dict: Result with success status and message ID
        """
        try:
            if not self.authenticate_gmail():
                return {'success': False, 'error': 'Gmail authentication failed'}
            
            message = self._create_message(to, subject, body, cc)
            
            # Send email
            sent_message = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()
            
            message_id = sent_message.get('id')
            thread_id = sent_message.get('threadId')
            
            # Log to briefings
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_file = self.briefings / f'email_sent_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md'
            
            log_content = f'''---
type: email_sent_log
to: {to}
subject: {subject}
sent: {timestamp}
status: sent
message_id: {message_id}
---

# Email Sent Log

## Sent
{timestamp}

## Details
- **To:** {to}
- **Subject:** {subject}
- **Message ID:** {message_id}

## Content
{body}
'''
            log_file.write_text(log_content, encoding='utf-8')
            
            return {
                'success': True,
                'message_id': message_id,
                'thread_id': thread_id,
                'log_file': str(log_file)
            }
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return {'success': False, 'error': str(error)}
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def email_draft(self, to: str, subject: str, body: str,
                    cc: str = None, reply_to: str = None) -> dict:
        """
        Create an email draft in Pending_Approval/ folder.
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Email body text
            cc: CC recipients (optional)
            reply_to: Message ID to reply to (optional)
        
        Returns:
            dict: Result with draft file path
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            safe_subject = ''.join(c for c in subject if c.isalnum() or c in (' ', '-', '_')).strip()[:30]
            safe_subject = safe_subject.replace(' ', '_')
            filename = f'EMAIL_REPLY_{timestamp}_{safe_subject}.md'
            filepath = self.pending_approval / filename
            
            cc_line = f'\ncc: {cc}' if cc else ''
            reply_line = f'\nin_reply_to: {reply_to}' if reply_to else ''
            
            draft_content = f'''---
type: email_draft
to: {to}{cc_line}
subject: {subject}{reply_line}
created: {datetime.now().isoformat()}
status: pending_approval
---

# Email Draft

## To
{to}

## Subject
{subject}

## Body

{body}

---
## Instructions
1. Review and edit the content above
2. Move this file to /Approved to send
3. Move to /Rejected to discard

## To Send
After moving to /Approved/, run:
  python send_email.py <vault_path> --action send
'''
            filepath.write_text(draft_content, encoding='utf-8')
            
            return {
                'success': True,
                'draft_file': str(filepath),
                'filename': filename,
                'location': 'Pending_Approval/',
                'next_step': 'Move file to Approved/ folder to send, or Rejected/ to discard'
            }
            
        except Exception as e:
            logger.error(f"Draft creation failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def email_list(self, max_results: int = 10, query: str = 'is:unread') -> dict:
        """
        List recent emails from Gmail.
        
        Args:
            max_results: Maximum number of emails to return
            query: Gmail search query (default: is:unread)
        
        Returns:
            dict: List of emails
        """
        try:
            if not self.authenticate_gmail():
                return {'success': False, 'error': 'Gmail authentication failed'}
            
            results = self.gmail_service.users().messages().list(
                userId='me',
                q=query,
                maxResults=max_results
            ).execute()
            
            messages = results.get('messages', [])
            emails = []
            
            for msg in messages:
                # Get message details
                msg_data = self.gmail_service.users().messages().get(
                    userId='me',
                    id=msg['id'],
                    format='metadata',
                    metadataHeaders=['From', 'Subject', 'Date']
                ).execute()
                
                headers = {h['name']: h['value'] for h in msg_data.get('payload', {}).get('headers', [])}
                
                emails.append({
                    'id': msg['id'],
                    'from': headers.get('From', 'Unknown'),
                    'subject': headers.get('Subject', 'No Subject'),
                    'date': headers.get('Date', ''),
                    'snippet': msg_data.get('snippet', '')
                })
            
            return {
                'success': True,
                'count': len(emails),
                'emails': emails
            }
            
        except HttpError as error:
            logger.error(f"Gmail API error: {error}")
            return {'success': False, 'error': str(error)}
        except Exception as e:
            logger.error(f"Email list failed: {e}")
            return {'success': False, 'error': str(e)}


def handle_request(server: EmailMCPServer, request: dict) -> dict:
    """Handle an incoming MCP request."""
    method = request.get('method')
    params = request.get('params', {})
    request_id = request.get('id')
    
    try:
        # MCP initialization
        if method == 'initialize':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'protocolVersion': MCP_PROTOCOL_VERSION,
                    'capabilities': {
                        'tools': {}
                    },
                    'serverInfo': {
                        'name': 'email-mcp-server',
                        'version': '1.0.0'
                    }
                }
            }
        
        # Initialized notification
        if method == 'notifications/initialized':
            return None  # No response needed
        
        # Tools listing
        if method == 'tools/list':
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'tools': [
                        {
                            'name': 'email_send',
                            'description': 'Send an email immediately via Gmail API. Use this only for approved emails.',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'to': {
                                        'type': 'string',
                                        'description': 'Recipient email address'
                                    },
                                    'subject': {
                                        'type': 'string',
                                        'description': 'Email subject line'
                                    },
                                    'body': {
                                        'type': 'string',
                                        'description': 'Email body text'
                                    },
                                    'cc': {
                                        'type': 'string',
                                        'description': 'CC recipients (optional)'
                                    }
                                },
                                'required': ['to', 'subject', 'body']
                            }
                        },
                        {
                            'name': 'email_draft',
                            'description': 'Create an email draft in Pending_Approval/ for human review. ALWAYS use this for outgoing emails - never send directly.',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'to': {
                                        'type': 'string',
                                        'description': 'Recipient email address'
                                    },
                                    'subject': {
                                        'type': 'string',
                                        'description': 'Email subject line'
                                    },
                                    'body': {
                                        'type': 'string',
                                        'description': 'Email body text'
                                    },
                                    'cc': {
                                        'type': 'string',
                                        'description': 'CC recipients (optional)'
                                    },
                                    'reply_to': {
                                        'type': 'string',
                                        'description': 'Message ID to reply to (optional)'
                                    }
                                },
                                'required': ['to', 'subject', 'body']
                            }
                        },
                        {
                            'name': 'email_list',
                            'description': 'List recent emails from Gmail inbox.',
                            'inputSchema': {
                                'type': 'object',
                                'properties': {
                                    'max_results': {
                                        'type': 'integer',
                                        'description': 'Maximum number of emails to return (default: 10)'
                                    },
                                    'query': {
                                        'type': 'string',
                                        'description': 'Gmail search query (default: is:unread)'
                                    }
                                }
                            }
                        }
                    ]
                }
            }
        
        # Tool calls
        if method == 'tools/call':
            tool_name = params.get('name')
            tool_args = params.get('arguments', {})
            
            if tool_name == 'email_send':
                result = server.email_send(
                    to=tool_args.get('to'),
                    subject=tool_args.get('subject'),
                    body=tool_args.get('body'),
                    cc=tool_args.get('cc')
                )
            elif tool_name == 'email_draft':
                result = server.email_draft(
                    to=tool_args.get('to'),
                    subject=tool_args.get('subject'),
                    body=tool_args.get('body'),
                    cc=tool_args.get('cc'),
                    reply_to=tool_args.get('reply_to')
                )
            elif tool_name == 'email_list':
                result = server.email_list(
                    max_results=tool_args.get('max_results', 10),
                    query=tool_args.get('query', 'is:unread')
                )
            else:
                result = {'success': False, 'error': f'Unknown tool: {tool_name}'}
            
            # Format response for MCP
            content = [
                {
                    'type': 'text',
                    'text': json.dumps(result, indent=2)
                }
            ]
            
            return {
                'jsonrpc': '2.0',
                'id': request_id,
                'result': {
                    'content': content,
                    'isError': not result.get('success', False)
                }
            }
        
        # Unknown method
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32601,
                'message': f'Method not found: {method}'
            }
        }
        
    except Exception as e:
        logger.error(f"Request handling failed: {e}")
        return {
            'jsonrpc': '2.0',
            'id': request_id,
            'error': {
                'code': -32603,
                'message': f'Internal error: {str(e)}'
            }
        }


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Email MCP Server for AI Employee')
    parser.add_argument('--vault-path', type=str, help='Path to Obsidian vault')
    
    args = parser.parse_args()
    
    # Initialize server
    server = EmailMCPServer(vault_path=args.vault_path)
    
    logger.info("Email MCP Server starting...")
    logger.info("Listening for requests on stdin/stdout")
    
    # Read requests from stdin
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        
        try:
            request = json.loads(line)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON: {e}")
            continue
        
        # Handle request
        response = handle_request(server, request)
        
        # Send response to stdout
        if response:
            print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
