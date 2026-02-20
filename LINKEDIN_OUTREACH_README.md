# LinkedIn Buyer Outreach System

An automated system to find potential buyers on LinkedIn and send personalized cold outreach messages without being flagged as spam.

---

## What You Need to Provide

Before running the system, you need to prepare the following:

### 1. LinkedIn Account Credentials

- **LinkedIn email** and **password** for the account that will send outreach
- Ideally, use a well-established LinkedIn account (6+ months old, 200+ connections)
- Make sure the account has a complete, professional profile

### 2. Your Ideal Buyer Persona

Define who you want to reach:

| What to Define | Examples |
|---|---|
| **Job titles** to target | "CTO", "VP of Engineering", "Head of Product" |
| **Industries** | "Software Development", "Financial Services", "Healthcare" |
| **Locations** | "United States", "United Kingdom", "Germany" |
| **Company sizes** | "51-200", "201-500", "501-1000" employees |
| **Keywords** in profiles | "cloud migration", "AI/ML", "DevOps" |
| **Keywords to exclude** | "Recruiter", "Freelance", "Student" |

### 3. Your Service Description

- **Your company name** (e.g., "Acme Solutions")
- **One-liner of your service** (e.g., "AI-powered workflow automation")
- This is injected into your message templates

### 4. Message Templates

Write 2-3 connection request note variants and 1-2 follow-up messages. The system uses Jinja2 templates with these variables:

| Variable | Description |
|---|---|
| `{{ first_name }}` | Prospect's first name |
| `{{ last_name }}` | Prospect's last name |
| `{{ job_title }}` | Current job title |
| `{{ company }}` | Current company |
| `{{ industry }}` | Industry |
| `{{ location }}` | Location |
| `{{ mutual_count }}` | Mutual connections count |
| `{{ headline }}` | Profile headline |
| `{{ your_name }}` | Your name (auto-detected) |
| `{{ your_company }}` | Your company name |
| `{{ service }}` | Your service description |

**Connection notes must be under 300 characters** (LinkedIn limit).

---

## Quick Start

### Step 1: Install Dependencies

```bash
cd linkedin_outreach
pip install -r requirements.txt
```

### Step 2: Create Your Config

```bash
cp campaign_config.example.yaml campaign_config.yaml
```

Edit `campaign_config.yaml` with your details (credentials, search criteria, messages).

### Step 3: Set Credentials (recommended via env vars)

```bash
export LINKEDIN_EMAIL="your@email.com"
export LINKEDIN_PASSWORD="your_password"
```

### Step 4: Preview Your Messages

```bash
python -m linkedin_outreach preview
```

This shows how your templates render with sample data, without sending anything.

### Step 5: Search for Prospects (no outreach)

```bash
python -m linkedin_outreach search
```

This finds matching profiles and saves them locally without sending any messages.

### Step 6: Run a Single Outreach Cycle

```bash
python -m linkedin_outreach run
```

### Step 7: Run Continuous Outreach

```bash
python -m linkedin_outreach run --cycles 0
```

### Other Commands

```bash
# View campaign statistics
python -m linkedin_outreach stats

# Export prospects to CSV
python -m linkedin_outreach export

# Verbose logging
python -m linkedin_outreach -v run
```

---

## How the Anti-Spam System Works

The system uses multiple layers to avoid LinkedIn spam detection:

### 1. Conservative Rate Limits (defaults)
- **20 connection requests/day** (LinkedIn's safe zone is ~25)
- **30 messages/day** (well under LinkedIn's threshold)
- **80 profile views/day** (under the 100 flag threshold)

### 2. Warmup Period
- New campaigns start at **20% of max limits**
- Gradually ramp up to 100% over **14 days**
- This mimics organic growth in activity

### 3. Human-like Timing
- Random delays between **45-180 seconds** between every action
- Gaussian jitter so delays aren't perfectly uniform
- Only operates during **business hours** (8 AM - 8 PM)
- Only active on **weekdays** (configurable)

### 4. Message Variation
- **Multiple templates** are rotated randomly
- **Synonym substitution** slightly alters wording each time
- **Profile-specific personalization** makes every message unique
- No two prospects receive identical messages

### 5. Working Hours Enforcement
- The system pauses outside configured working hours
- Resumes automatically when the next working window starts

---

## Multi-Account Mode (3-5 Accounts)

For faster results, you can run up to 5 accounts in parallel. The system handles:
- **Audience segmentation** -- each account targets a different niche so they never contact the same person
- **Staggered time windows** -- accounts operate in different hours to avoid pattern detection
- **Per-account proxies** -- each account routes through a different residential IP
- **Shared de-duplication** -- a single prospect database ensures no overlap
- **Sequential execution** -- accounts run one at a time with random gaps between them

### What You Need for Multi-Account

| Per Account | Description |
|---|---|
| LinkedIn credentials | Email + password for each account |
| Residential proxy | A unique proxy IP (e.g., from Bright Data, Smartproxy, IPRoyal) |
| Audience segment | Different job titles, industries, or locations per account |
| Time window | Stagger hours so accounts aren't active simultaneously |

### Multi-Account Setup

1. Uncomment the `accounts` section in `campaign_config.yaml` (see the example config)
2. Fill in credentials, proxy, segment, and time window for each account
3. Run with multi-account commands:

```bash
# Run one cycle across all accounts
python -m linkedin_outreach multi-run

# Run continuously
python -m linkedin_outreach multi-run --cycles 0

# View per-account statistics
python -m linkedin_outreach multi-stats
```

### Recommended 5-Account Layout

| Account | Segment | Hours | Why |
|---|---|---|---|
| 1 | Fintech CTOs | 8 AM - 12 PM | Financial services decision-makers |
| 2 | SaaS Directors | 10 AM - 2 PM | Software company mid-level leaders |
| 3 | Healthcare Tech | 12 PM - 4 PM | Healthcare IT decision-makers |
| 4 | UK Tech Leaders | 2 PM - 6 PM | Different geography = zero overlap |
| 5 | E-commerce VPs | 4 PM - 8 PM | Retail/e-commerce vertical |

This gives you ~100 connection requests/day across 5 distinct audiences with zero overlap.

---

## Project Structure

```
linkedin_outreach/
├── __init__.py
├── __main__.py              # Entry point
├── cli.py                   # CLI commands (run, multi-run, stats, multi-stats, etc.)
├── config.py                # Configuration (single + multi-account)
├── campaign.py              # Single-account campaign orchestrator
├── multi_account.py         # Multi-account manager with segmentation
├── linkedin_client.py       # LinkedIn API wrapper with proxy support
├── prospect_finder.py       # Search and filter prospects
├── prospect_store.py        # Shared prospect database (JSON file)
├── message_engine.py        # Template rendering and variation
├── rate_limiter.py          # Per-account rate limiting and warmup
├── campaign_config.example.yaml  # Example config with multi-account section
├── requirements.txt
├── data/                    # Prospect data (auto-created)
└── logs/                    # Campaign logs (auto-created)
```

---

## Best Practices for Not Getting Flagged

1. **Start slow**: Let the warmup period do its job. Don't override the limits.
2. **Write genuine messages**: Templates should sound like a real person wrote them.
3. **Keep connection notes short**: Under 200 chars is ideal (300 max).
4. **Don't sell in the connection request**: Just express interest in connecting.
5. **Sell in follow-ups**: Once connected, send a value-first follow-up.
6. **Target precisely**: Better to message 20 perfect-fit prospects than 100 random ones.
7. **Use a warmed-up account**: Accounts with 500+ connections and 6+ months of activity are safest.
8. **Engage manually too**: Like posts, comment, share content. Mixed activity looks organic.
9. **Monitor your SSI score**: LinkedIn's Social Selling Index affects what you can do.
10. **Don't run 24/7**: Use working hours only, take weekends off.

---

## Troubleshooting

| Issue | Solution |
|---|---|
| Login fails | Check credentials; LinkedIn may require 2FA or CAPTCHA. Solve it manually first, then retry. |
| "CHALLENGE" error | LinkedIn detected automation. Wait 24-48 hours, then login manually to clear challenges. |
| Low acceptance rate | Improve your profile, refine targeting, or rewrite connection notes. |
| Account restricted | Stop all automation immediately. Wait 1-2 weeks. Contact LinkedIn support if needed. |
| Rate limit hit early | The warmup period intentionally limits you. Let it ramp up naturally. |

---

## Safety Warning

This system uses the unofficial `linkedin-api` Python library. While it implements many safeguards, automated LinkedIn outreach always carries some risk of account restrictions. Use responsibly and at your own discretion. The conservative defaults are tuned to minimize risk, but no automation can guarantee zero risk.
