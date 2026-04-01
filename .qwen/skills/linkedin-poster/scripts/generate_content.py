#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Content Generator - Generate LinkedIn post drafts.

This script helps generate LinkedIn post drafts based on topics,
achievements, or business updates.

Usage:
    python generate_content.py <vault_path> --topic "Your topic here"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime


def generate_post_content(topic: str, post_type: str = 'achievement') -> str:
    """
    Generate LinkedIn post content based on topic and type.
    
    Args:
        topic: The main topic/subject
        post_type: Type of post (achievement, update, thought_leadership)
    
    Returns:
        str: Generated post content
    """
    templates = {
        'achievement': f'''🎉 Exciting News!

I'm thrilled to share that I've accomplished: {topic}

This milestone represents:
✅ Hard work and dedication
✅ Learning and growth
✅ New opportunities ahead

Key takeaways from this journey:
• Lesson learned #1
• Lesson learned #2  
• Lesson learned #3

Thank you to everyone who supported me along the way!

#Achievement #Growth #Milestone #ProfessionalDevelopment''',
        
        'update': f'''📈 Business Update

Here's what's happening with: {topic}

What we're working on:
🔹 Current focus area
🔹 Recent progress
🔹 Next steps

Why this matters:
[Brief explanation of impact]

Stay tuned for more updates!

#BusinessUpdate #Innovation #Progress''',
        
        'thought_leadership': f'''💭 Industry Insight: {topic}

After working in this space, here's what I've learned:

**The Challenge:**
Many professionals struggle with [common problem related to topic].

**The Solution:**
Through experience, I've found that [key insight/solution].

**The Future:**
Looking ahead, I believe [prediction/trend].

What's your perspective on {topic}? Share your thoughts below!

#ThoughtLeadership #Industry #Innovation #Future''',
        
        'lesson': f'''📚 Lesson Learned: {topic}

Today I learned something valuable about: {topic}

Here's what surprised me:
• Unexpected insight #1
• Unexpected insight #2
• Unexpected insight #3

How I'll apply this:
[Practical application]

What's a recent lesson you've learned?

#Learning #Growth #ProfessionalDevelopment #LessonsLearned''',
        
        'question': f'''❓ Quick Question for My Network

Regarding {topic}:

[Ask your question here]

I'm curious to hear different perspectives from my network.

Drop your thoughts in the comments! 👇

#Discussion #Networking #Community''',
    }
    
    return templates.get(post_type, templates['achievement'])


def create_draft_file(vault_path: Path, topic: str, post_type: str, content: str) -> Path:
    """
    Create a draft LinkedIn post file.
    
    Args:
        vault_path: Path to vault
        topic: Post topic
        post_type: Type of post
        content: Generated content
    
    Returns:
        Path: Path to created file
    """
    pending_approval = vault_path / 'Pending_Approval'
    pending_approval.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    safe_topic = topic.replace(' ', '_').replace('/', '_')[:30]
    filename = f'LINKEDIN_{timestamp}_{safe_topic}.md'
    filepath = pending_approval / filename
    
    file_content = f'''---
type: linkedin_post
topic: {topic}
post_type: {post_type}
status: draft
created: {datetime.now().isoformat()}
---

# LinkedIn Post Draft

## Topic
{topic}

## Post Content

{content}

---
## Instructions
1. Review and edit the content above
2. Customize the bullet points with your specific details
3. Add relevant personal experiences
4. Move this file to /Approved to post
5. Move to /Rejected to discard
'''
    
    filepath.write_text(file_content, encoding='utf-8')
    return filepath


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='LinkedIn Content Generator')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--topic', type=str, required=True,
                       help='Post topic/subject')
    parser.add_argument('--type', type=str, 
                       choices=['achievement', 'update', 'thought_leadership', 'lesson', 'question'],
                       default='achievement', help='Type of post')
    parser.add_argument('--output', type=str, help='Output file path (optional)')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path)
    
    # Generate content
    print(f"Generating {args.type} post about: {args.topic}")
    content = generate_post_content(args.topic, args.type)
    
    print("\n=== Generated Content ===\n")
    print(content)
    print("\n========================\n")
    
    # Create draft file
    filepath = create_draft_file(vault_path, args.topic, args.type, content)
    
    print(f"Draft saved to: {filepath}")
    print("\nNext steps:")
    print("1. Edit the draft file to customize content")
    print("2. Move to /Approved folder when ready to post")
    print("3. Run: python post_linkedin.py <vault> --action post")


if __name__ == "__main__":
    main()
