---
name: linkedin-poster
description: |
  Create and post LinkedIn content automatically to generate business leads. 
  Drafts posts based on business updates, achievements, or topics. Supports 
  scheduling and requires approval before posting. Uses Playwright for browser 
  automation. Use this skill when user mentions LinkedIn, social media posting, 
  business content, lead generation, or professional networking.
---

# LinkedIn Poster Skill

Create and schedule LinkedIn posts for business growth using Playwright browser automation.

## Prerequisites

```bash
# Install Playwright
pip install playwright
playwright install chromium
```

## Configuration

### Environment Variables (.env)
```bash
# LinkedIn credentials (optional - can login manually)
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password

# Vault configuration
VAULT_PATH=./AI_Employee_Vault
POSTING_SCHEDULE=daily
```

## Quick Start

### Step 1: Create Post Draft

```bash
qwen "Create a LinkedIn post about completing the Bronze Tier AI Employee"
```

This creates a draft in `Pending_Approval/`:

```markdown
---
type: linkedin_post
topic: achievement
status: draft
created: 2026-03-30
---

# LinkedIn Post Draft

## Topic
Completing Bronze Tier AI Employee

## Post Content

🎉 Exciting Milestone!

I've just completed the Bronze Tier of my AI Employee project...

#AI #Automation #Innovation

---
## Instructions
1. Review and edit content
2. Move to /Approved to post
3. Move to /Rejected to discard
```

### Step 2: Review and Approve

1. Open the draft file in `Pending_Approval/`
2. Review and edit the content
3. **To Post:** Move file to `Approved/` folder
4. **To Discard:** Move file to `Rejected/` folder

### Step 3: Post to LinkedIn

```bash
cd .qwen/skills/linkedin-poster
python scripts/post_linkedin.py ../../../AI_Employee_Vault --action post
```

## Usage

### Create Post Draft

```bash
qwen "Create a LinkedIn post about completing the Bronze Tier AI Employee"
```

### Review Drafts

```bash
qwen "Show me draft LinkedIn posts in Pending_Approval/"
```

### Post After Approval

```bash
qwen "Post the approved LinkedIn content"
```

### Generate Content Ideas

```bash
qwen "Generate 5 LinkedIn post ideas about AI automation"
```

## Post Templates

### Achievement Post
```markdown
---
type: linkedin_post
topic: achievement
status: draft
---

# 🎉 Milestone Achieved!

I'm excited to share that I've completed [ACHIEVEMENT]!

## What I Learned
- Key lesson 1
- Key lesson 2
- Key lesson 3

## What's Next
[Brief mention of next goal]

#Hashtag1 #Hashtag2 #Hashtag3
```

### Business Update Post
```markdown
---
type: linkedin_post
topic: business_update
status: draft
---

# 📈 Business Update

Quick update on [PROJECT/INITIATIVE]:

✅ What's working
🚀 What's launching soon
💡 What we're learning

Interested in [TOPIC]? Let's connect!

#Business #Innovation #Growth
```

### Thought Leadership Post
```markdown
---
type: linkedin_post
topic: thought_leadership
status: draft
---

# 💭 Industry Insight

Here's what I'm seeing in [INDUSTRY/TREND]:

**The Problem:**
[Brief description]

**The Solution:**
[Your perspective]

**The Future:**
[Where things are heading]

What's your take? Share in comments!

#Leadership #Innovation #Future
```

## Workflow

```
Qwen drafts post based on topic
       ↓
Save to Pending_Approval/
       ↓
Human reviews and moves to Approved/
       ↓
Qwen posts via Playwright
       ↓
Log to Briefings/
       ↓
Move to Done/
```

## Hashtag Guidelines

| Category | Hashtags |
|----------|----------|
| Business | #Business #Entrepreneurship #Growth |
| Tech | #AI #Technology #Innovation #Automation |
| Career | #Career #ProfessionalDevelopment #Learning |
| Personal | #Productivity #LifeHacks #Success |

Use 3-5 relevant hashtags per post.

## Posting Schedule

| Frequency | Best Times |
|-----------|------------|
| Daily | 8-9 AM, 12 PM, 5-6 PM |
| Weekly | Tuesday-Thursday mornings |
| Bi-weekly | Wednesday 10 AM |

## Scripts

| Script | Purpose |
|--------|---------|
| `authenticate_linkedin.py` | One-time LinkedIn authentication |
| `post_linkedin.py` | Post approved content to LinkedIn |
| `generate_content.py` | AI content generation for posts |

### Authentication (First Time)

```bash
cd .qwen/skills/linkedin-poster/scripts
python authenticate_linkedin.py
```

**Session saved to:** `data/.linkedin_session/` (runtime state, not in skill folder)

### Posting

```bash
python post_linkedin.py ../../../AI_Employee_Vault --action post
```

## Security Notes

- Store credentials in .env (never commit)
- Use app-specific passwords if available
- Review posts before publishing
- Respect LinkedIn Terms of Service
- Browser session saved locally

## Integration

Works with:
- **approval-workflow**: Require approval before posting
- **browsing-with-playwright**: Post via browser automation
- **scheduler**: Schedule regular posts
- **plan-creator**: Plan content calendar

## Best Practices

1. **Authentic voice** - Write in your natural tone
2. **Add value** - Share insights, not just promotions
3. **Engage** - Respond to comments within 24 hours
4. **Visual content** - Include images when relevant
5. **Track metrics** - Monitor engagement and adjust
6. **Human approval** - Always review before posting

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Login failed | Clear browser session, try manual login |
| Post not publishing | Check LinkedIn session is active |
| Element not found | Update Playwright: `playwright install chromium` |
| Rate limited | Wait 24 hours between posts |

## Example: Full LinkedIn Workflow

### Step 1: Create Post

```bash
qwen "Create a LinkedIn post about our AI Employee Silver Tier completion"
```

Creates: `Pending_Approval/LINKEDIN_20260330_silver_tier.md`

### Step 2: Review

```markdown
# Review the draft
- Check content accuracy
- Verify hashtags
- Edit tone if needed
```

### Step 3: Approve

```
Move file from Pending_Approval/ to Approved/
```

### Step 4: Post

```bash
python scripts/post_linkedin.py ../../../AI_Employee_Vault --action post
```

### Step 5: Confirmation

```
✅ Post published successfully!
Logged to: Briefings/linkedin_post_20260330_103000.md
Moved to: Done/LINKEDIN_20260330_silver_tier.md
```
