---
name: linkedin-poster
description: |
  Create and post LinkedIn content automatically to generate business leads. Drafts posts 
  based on business updates, achievements, or topics. Supports scheduling and requires 
  approval before posting. Use this skill when user mentions LinkedIn, social media posting, 
  business content, lead generation, or professional networking.
---

# LinkedIn Poster Skill

Create and schedule LinkedIn posts for business growth.

## Prerequisites

```bash
# Install Playwright for browser automation
pip install playwright
playwright install chromium
```

## Configuration

### Environment Variables (.env)
```bash
LINKEDIN_EMAIL=your.email@example.com
LINKEDIN_PASSWORD=your_password
VAULT_PATH=./AI_Employee_Vault
POSTING_SCHEDULE=daily
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

## Post Templates

### Achievement Post
```markdown
---
type: linkedin_post
topic: achievement
status: draft
created: 2026-03-30
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

---
[Move to /Approved to post]
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
Qwen posts via LinkedIn
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
| `post_linkedin.py` | Browser automation for posting |
| `generate_content.py` | AI content generation |

## Security Notes

- Store credentials in .env (never commit)
- Use app-specific passwords if available
- Review posts before publishing
- Respect LinkedIn Terms of Service

## Integration

Works with:
- **approval-workflow**: Require approval before posting
- **browsing-with-playwright**: Post via browser automation
- **scheduler**: Schedule regular posts

## Best Practices

1. **Authentic voice** - Write in your natural tone
2. **Add value** - Share insights, not just promotions
3. **Engage** - Respond to comments within 24 hours
4. **Visual content** - Include images when relevant
5. **Track metrics** - Monitor engagement and adjust
