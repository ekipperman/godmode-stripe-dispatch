# ?? SuperScraperBot   AI Telegram Influencer Assistant

SuperScraperBot is a production-ready Telegram bot that helps you scrape influencer profiles from Instagram or TikTok, filter them by followers and keywords, generate custom outreach messages using OpenAI, and save leads to Supabase   all directly from Telegram.

Built for speed. Designed for scale. ?

---

## ?? Features

| Command               | Description                                          |
|------------------------|------------------------------------------------------|
| `/start`               | Welcome message                                      |
| `/scrape @handle`      | Scrape influencer profile (IG/TikTok)               |
| `/sendbuttons`         | Choose platform via inline buttons                  |
| `/setfollowers 1000`   | Set minimum follower count filter                   |
| `/setkeywords fashion fitness` | Set keyword filters (bio-based)         |
| `/reviewleads`         | View recent leads from Supabase                     |
| `/outreach @handle`    | Generate a GPT-powered outreach DM                  |
| `/client client123`    | Route scraped leads to a Telegram channel by ID     |
| `/help`                | Show all commands (optional plugin)                 |

---

## ?? Built-In Advanced Capabilities

| Feature                | Description                                          |
|------------------------|------------------------------------------------------|
| ? Supabase Integration | Stores all qualified leads with full details        |
| ? OpenAI Messaging     | Uses GPT to write custom DMs for each influencer    |
| ? Filtering            | Smart filters by follower count and keyword match   |
| ? Inline UI            | Platform selection with buttons                     |
| ? Plugin Architecture  | Easily extend with drop-in command modules          |
| ? Multi-Client Routing | Map different clients to different Telegram chats   |
| ? GPT-4 + Vision Ready | Supports GPT-4, GPT-4o, image inputs, TTS, and Whisper |

---

## ?? Folder Structure

\`\`\`
project-root/
 
+-- bot/
    +-- telegram_bot.py           # Main bot logic
    +-- plugin_manager.py         # Auto-loads plugins
    +-- plugins/                  # Modular Telegram commands
        +-- scrape_influencer.py
        +-- review_leads.py
        +-- outreach_dm.py
        +-- send_buttons.py
        +-- set_filters.py
        +-- (optional plugins...)
 
+-- services/
    +-- scrape.py                 # Scraper logic (mock, instaloader, playwright)
    +-- filters.py                # Filter functions
    +-- supabase_sync.py          # Save + fetch from Supabase
    +-- openai_utils.py           # GPT content generation (DMs, summaries, etc.)
 
+-- .env.example                  # Environment variable template
+-- requirements.txt              # Python dependencies
+-- Dockerfile                    # Container-ready setup (optional)
+-- run.py / main.py              # App entry point
+-- README.md                     # You're here!
\`\`\`

---

## ?? Setup

### 1. Clone the repository
\`\`\`bash
git clone https://github.com/your-username/SuperScraperBot.git
cd SuperScraperBot
\`\`\`

### 2. Create and configure \`.env\`
Fill in:
- TELEGRAM_BOT_TOKEN
- OPENAI_API_KEY
- SUPABASE_URL
- SUPABASE_KEY
- CLIENT_CHANNELS

### 3. Install dependencies
\`\`\`bash
pip install -r requirements.txt
\`\`\`

### 4. Run the bot
\`\`\`bash
python bot/telegram_bot.py
\`\`\`

---

## ?? Want More?

- Add \`/exportleads\` to CSV
- Build a Supabase dashboard
- Deploy on Railway, Render, or Fly.io
- Sync to Notion or CRM

---

## ?? Preview

![Screenshot](https://your-screenshot-url-here.com/superbot-ui-preview.png)

---

## ?? Deploy

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template-link)

---

## ?? Made With

- ?? OpenAI
- ?? Supabase
- ?? python-telegram-bot
- ?? Modular plugin architecture

---

  2025   Built by [Eric Kipperman]
