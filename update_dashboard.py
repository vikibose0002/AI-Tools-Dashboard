"""
AI Tools Dashboard Auto-Updater
================================
- Scrapes official pricing pages for accurate data
- Uses NVIDIA API to structure scraped content into clean JSON
- Fetches Reddit community feedback live
- Outputs data.json (loaded by index.html to update dashboard)
- Updates index.html banner with IST timestamp
- Tracks all 50 tools from official sources
"""

import os, json, re, time, requests
from datetime import datetime, timezone, timedelta
from html.parser import HTMLParser

# ── TIMEZONE ────────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

# ── CREDENTIALS ─────────────────────────────────────────────────
NVIDIA_KEY  = os.environ['GEMINI_API_KEY']        # secret still named GEMINI_API_KEY
TG_TOKEN    = os.environ['TELEGRAM_BOT_TOKEN']
TG_CHAT     = os.environ['TELEGRAM_CHAT_ID']
GITHUB_USER = os.environ.get('GITHUB_USERNAME', 'yourusername')

# ── NVIDIA NIM API ───────────────────────────────────────────────
NVIDIA_URL   = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
# Fallback models if above returns 404:
# "nvidia/llama-3.1-nemotron-70b-instruct"
# "mistralai/mixtral-8x22b-instruct-v0.1"

# ── SCRAPING HEADERS ────────────────────────────────────────────
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

# ── ALL 50 TOOLS — exact list from user ─────────────────────────
TOOLS = [
  # ── GENERAL AI ──────────────────────────────────────────────
  {
    "id":"chatgpt","name":"ChatGPT","cat":"general","maker":"OpenAI",
    "home":"https://chatgpt.com/",
    "sources":{
      "Pricing Page":    "https://openai.com/chatgpt/pricing",
      "Enterprise Info": "https://openai.com/enterprise",
      "Help Center":     "https://help.openai.com/en/articles/11165333-chatgpt-enterprise-and-edu-models-limits",
      "Reddit":          "https://www.reddit.com/r/ChatGPT/"
    },
    "pricing_url":"https://openai.com/chatgpt/pricing",
    "reddit_query":"ChatGPT pricing plans usage limits 2025"
  },
  {
    "id":"claude","name":"Claude","cat":"general","maker":"Anthropic",
    "home":"https://claude.ai/new",
    "sources":{
      "Pricing Page":    "https://claude.ai/pricing",
      "Enterprise Plan": "https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan",
      "API Pricing":     "https://docs.anthropic.com/en/docs/about-claude/pricing",
      "Reddit":          "https://www.reddit.com/r/ClaudeAI/"
    },
    "pricing_url":"https://claude.ai/pricing",
    "reddit_query":"Claude AI pricing plans rate limits usage 2025"
  },
  {
    "id":"gemini","name":"Google Gemini","cat":"general","maker":"Google",
    "home":"https://gemini.google.com/app?hl=en-IN",
    "sources":{
      "Pricing Page":    "https://one.google.com/intl/en/about/google-ai-plans/",
      "Workspace AI":    "https://workspace.google.com/intl/en/pricing",
      "Enterprise":      "https://workspace.google.com/products/gemini/",
      "Reddit":          "https://www.reddit.com/r/Gemini/"
    },
    "pricing_url":"https://one.google.com/intl/en/about/google-ai-plans/",
    "reddit_query":"Google Gemini AI pricing plans review 2025"
  },
  {
    "id":"m365","name":"Microsoft 365 Copilot","cat":"general","maker":"Microsoft",
    "home":"https://m365.cloud.microsoft/chat",
    "sources":{
      "Pricing Page":    "https://www.microsoft.com/en-us/microsoft-365-copilot/pricing-new",
      "Enterprise":      "https://www.microsoft.com/en-us/microsoft-365-copilot/pricing/enterprise",
      "Blog":            "https://www.microsoft.com/en-us/microsoft-365/blog/",
      "Reddit":          "https://www.reddit.com/r/Office365/"
    },
    "pricing_url":"https://www.microsoft.com/en-us/microsoft-365-copilot/pricing-new",
    "reddit_query":"Microsoft 365 Copilot pricing plans review limitations 2025"
  },

  # ── RESEARCH & SEARCH ────────────────────────────────────────
  {
    "id":"perplexity","name":"Perplexity","cat":"research","maker":"Perplexity AI",
    "home":"https://www.perplexity.ai/",
    "sources":{
      "Pricing Page":    "https://www.perplexity.ai/pro",
      "Enterprise":      "https://www.perplexity.ai/enterprise/pricing",
      "Help Center":     "https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you",
      "Reddit":          "https://www.reddit.com/r/perplexity_ai/"
    },
    "pricing_url":"https://www.perplexity.ai/enterprise/pricing",
    "reddit_query":"Perplexity AI pro pricing plans review limits 2025"
  },
  {
    "id":"notebooklm","name":"NotebookLM","cat":"research","maker":"Google",
    "home":"https://notebooklm.google/plans",
    "sources":{
      "Plans Page":      "https://notebooklm.google/plans",
      "Product Page":    "https://notebooklm.google/",
      "Help":            "https://support.google.com/notebooklm",
      "Reddit":          "https://www.reddit.com/r/notebooklm/"
    },
    "pricing_url":"https://notebooklm.google/plans",
    "reddit_query":"NotebookLM review features limitations 2025"
  },
  {
    "id":"elicit","name":"Elicit","cat":"research","maker":"Elicit",
    "home":"https://elicit.com/",
    "sources":{
      "Pricing Page":    "https://elicit.com/pricing",
      "Features":        "https://elicit.com/",
      "Reddit":          "https://www.reddit.com/r/PhD/"
    },
    "pricing_url":"https://elicit.com/pricing",
    "reddit_query":"Elicit AI research tool review pricing 2025"
  },
  {
    "id":"consensus","name":"Consensus","cat":"research","maker":"Consensus",
    "home":"https://consensus.app/",
    "sources":{
      "Pricing Page":    "https://consensus.app/home/pricing/",
      "Product Page":    "https://consensus.app/",
      "Reddit":          "https://www.reddit.com/r/academia/"
    },
    "pricing_url":"https://consensus.app/home/pricing/",
    "reddit_query":"Consensus app AI research pricing review 2025"
  },

  # ── WRITING & CONTENT ────────────────────────────────────────
  {
    "id":"grammarly","name":"Grammarly","cat":"content","maker":"Grammarly",
    "home":"https://www.grammarly.com/",
    "sources":{
      "Pricing Page":    "https://www.grammarly.com/plans",
      "Business":        "https://www.grammarly.com/business",
      "Enterprise":      "https://www.grammarly.com/enterprise",
      "Reddit":          "https://www.reddit.com/r/writing/"
    },
    "pricing_url":"https://www.grammarly.com/plans",
    "reddit_query":"Grammarly pricing plans review 2025"
  },
  {
    "id":"jasper","name":"Jasper","cat":"content","maker":"Jasper.ai",
    "home":"https://www.jasper.ai/",
    "sources":{
      "Pricing Page":    "https://www.jasper.ai/pricing",
      "Features":        "https://www.jasper.ai/features",
      "Reddit":          "https://www.reddit.com/r/marketing/"
    },
    "pricing_url":"https://www.jasper.ai/pricing",
    "reddit_query":"Jasper AI pricing review pros cons 2025"
  },
  {
    "id":"writesonic","name":"Writesonic","cat":"content","maker":"Writesonic",
    "home":"https://writesonic.com/",
    "sources":{
      "Pricing Page":    "https://writesonic.com/pricing",
      "Features":        "https://writesonic.com/features",
      "Reddit":          "https://www.reddit.com/r/SEO/"
    },
    "pricing_url":"https://writesonic.com/pricing",
    "reddit_query":"Writesonic pricing review SEO content 2025"
  },
  {
    "id":"copyai","name":"Copy.ai","cat":"content","maker":"Copy.ai",
    "home":"https://www.copy.ai/",
    "sources":{
      "Pricing Page":    "https://www.copy.ai/pricing",
      "Features":        "https://www.copy.ai/features",
      "Reddit":          "https://www.reddit.com/r/Entrepreneur/"
    },
    "pricing_url":"https://www.copy.ai/pricing",
    "reddit_query":"Copy.ai pricing GTM review pros cons 2025"
  },
  {
    "id":"notionai","name":"Notion AI","cat":"content","maker":"Notion",
    "home":"https://www.notion.com/",
    "sources":{
      "Pricing Page":    "https://www.notion.com/pricing",
      "AI Features":     "https://www.notion.com/product/ai",
      "Reddit":          "https://www.reddit.com/r/Notion/"
    },
    "pricing_url":"https://www.notion.com/pricing",
    "reddit_query":"Notion AI review pricing features 2025"
  },

  # ── CODING & DEVELOPMENT ─────────────────────────────────────
  {
    "id":"ghcopilot","name":"GitHub Copilot","cat":"coding","maker":"Microsoft",
    "home":"https://github.com/features/copilot",
    "sources":{
      "Plans Page":      "https://github.com/features/copilot/plans",
      "Docs":            "https://docs.github.com/en/copilot",
      "Enterprise":      "https://docs.github.com/en/enterprise-cloud@latest/copilot",
      "Reddit":          "https://www.reddit.com/r/programming/"
    },
    "pricing_url":"https://github.com/features/copilot/plans",
    "reddit_query":"GitHub Copilot pricing review enterprise 2025"
  },
  {
    "id":"cursor","name":"Cursor","cat":"coding","maker":"Anysphere",
    "home":"https://cursor.com/",
    "sources":{
      "Pricing Page":    "https://www.cursor.com/pricing",
      "Docs":            "https://docs.cursor.com/",
      "Reddit":          "https://www.reddit.com/r/cursor/"
    },
    "pricing_url":"https://www.cursor.com/pricing",
    "reddit_query":"Cursor AI IDE pricing review pros cons 2025"
  },
  {
    "id":"codex","name":"OpenAI Codex","cat":"coding","maker":"OpenAI",
    "home":"https://chatgpt.com/codex/",
    "sources":{
      "Codex Page":      "https://platform.openai.com/docs/models/codex",
      "API Pricing":     "https://openai.com/api/pricing/",
      "Blog":            "https://openai.com/blog/openai-codex",
      "Reddit":          "https://www.reddit.com/r/OpenAI/"
    },
    "pricing_url":"https://openai.com/api/pricing/",
    "reddit_query":"OpenAI Codex pricing features agent 2025"
  },
  {
    "id":"tabnine","name":"Tabnine","cat":"coding","maker":"Tabnine",
    "home":"https://www.tabnine.com/",
    "sources":{
      "Pricing Page":    "https://www.tabnine.com/pricing",
      "Enterprise":      "https://www.tabnine.com/enterprise",
      "Features":        "https://www.tabnine.com/features",
      "Reddit":          "https://www.reddit.com/r/programming/"
    },
    "pricing_url":"https://www.tabnine.com/pricing",
    "reddit_query":"Tabnine pricing enterprise on-premises review 2025"
  },
  {
    "id":"replit","name":"Replit Ghostwriter","cat":"coding","maker":"Replit",
    "home":"https://replit.com/ai",
    "sources":{
      "Pricing Page":    "https://replit.com/pricing",
      "AI Features":     "https://replit.com/ai",
      "Reddit":          "https://www.reddit.com/r/replit/"
    },
    "pricing_url":"https://replit.com/pricing",
    "reddit_query":"Replit Ghostwriter pricing review limitations 2025"
  },
  {
    "id":"codeium","name":"Codeium","cat":"coding","maker":"Codeium",
    "home":"https://codeium.en.softonic.com/web-apps",
    "sources":{
      "Pricing Page":    "https://codeium.com/pricing",
      "Windsurf":        "https://windsurf.com/pricing",
      "Features":        "https://codeium.com/",
      "Reddit":          "https://www.reddit.com/r/programming/"
    },
    "pricing_url":"https://codeium.com/pricing",
    "reddit_query":"Codeium Windsurf pricing free tier review 2025"
  },
  {
    "id":"claudecode","name":"Claude Code","cat":"coding","maker":"Anthropic",
    "home":"https://claude.com/product/claude-code",
    "sources":{
      "Product Page":    "https://claude.com/product/claude-code",
      "Pricing":         "https://claude.ai/pricing",
      "Docs":            "https://docs.anthropic.com/en/docs/claude-code/overview",
      "Reddit":          "https://www.reddit.com/r/ClaudeAI/"
    },
    "pricing_url":"https://claude.ai/pricing",
    "reddit_query":"Claude Code pricing agentic coding review 2025"
  },
  {
    "id":"autogen","name":"AutoGen","cat":"coding","maker":"Microsoft",
    "home":"https://autogenai.com/",
    "sources":{
      "GitHub":          "https://github.com/microsoft/autogen",
      "Docs":            "https://microsoft.github.io/autogen/",
      "Azure":           "https://azure.microsoft.com/en-us/products/ai-studio",
      "Reddit":          "https://www.reddit.com/r/LocalLLaMA/"
    },
    "pricing_url":"https://github.com/microsoft/autogen",
    "reddit_query":"AutoGen Microsoft multi-agent framework review 2025"
  },

  # ── WEB APP / NO-CODE ────────────────────────────────────────
  {
    "id":"v0","name":"v0","cat":"webapp","maker":"Vercel",
    "home":"https://v0.app/",
    "sources":{
      "Pricing Page":    "https://v0.dev/pricing",
      "Docs":            "https://v0.dev/docs",
      "Reddit":          "https://www.reddit.com/r/webdev/"
    },
    "pricing_url":"https://v0.dev/pricing",
    "reddit_query":"v0 Vercel pricing credits review frontend 2025"
  },
  {
    "id":"bubble","name":"Bubble","cat":"webapp","maker":"Bubble",
    "home":"https://bubble.io/",
    "sources":{
      "Pricing Page":    "https://bubble.io/pricing",
      "Features":        "https://bubble.io/features",
      "Reddit":          "https://www.reddit.com/r/nocode/"
    },
    "pricing_url":"https://bubble.io/pricing",
    "reddit_query":"Bubble no-code pricing review production apps 2025"
  },
  {
    "id":"softr","name":"Softr","cat":"webapp","maker":"Softr",
    "home":"https://www.softr.io/",
    "sources":{
      "Pricing Page":    "https://www.softr.io/pricing",
      "Features":        "https://www.softr.io/features",
      "Reddit":          "https://www.reddit.com/r/nocode/"
    },
    "pricing_url":"https://www.softr.io/pricing",
    "reddit_query":"Softr Airtable no-code pricing review 2025"
  },
  {
    "id":"durable","name":"Durable","cat":"webapp","maker":"Durable",
    "home":"https://durable.com/",
    "sources":{
      "Pricing Page":    "https://durable.co/pricing",
      "Features":        "https://durable.co/features",
      "Reddit":          "https://www.reddit.com/r/smallbusiness/"
    },
    "pricing_url":"https://durable.co/pricing",
    "reddit_query":"Durable AI website builder review pricing 2025"
  },

  # ── DESIGN & UI/UX ───────────────────────────────────────────
  {
    "id":"figmaai","name":"Figma AI","cat":"design","maker":"Figma",
    "home":"https://www.figma.com/ai/",
    "sources":{
      "AI Features":     "https://www.figma.com/ai/",
      "Pricing Page":    "https://www.figma.com/pricing/",
      "Reddit":          "https://www.reddit.com/r/UI_Design/"
    },
    "pricing_url":"https://www.figma.com/pricing/",
    "reddit_query":"Figma AI features pricing review designers 2025"
  },
  {
    "id":"uizard","name":"Uizard","cat":"design","maker":"Uizard",
    "home":"https://uizard.io/",
    "sources":{
      "Pricing Page":    "https://uizard.io/pricing/",
      "Features":        "https://uizard.io/features/",
      "Reddit":          "https://www.reddit.com/r/ProductManagement/"
    },
    "pricing_url":"https://uizard.io/pricing/",
    "reddit_query":"Uizard UI design AI pricing review 2025"
  },
  {
    "id":"canva","name":"Canva Magic Studio","cat":"design","maker":"Canva",
    "home":"https://www.canva.com/en_in/magic/",
    "sources":{
      "Magic Studio":    "https://www.canva.com/magic/",
      "Pricing Page":    "https://www.canva.com/pricing/",
      "Enterprise":      "https://www.canva.com/enterprise/",
      "Reddit":          "https://www.reddit.com/r/graphic_design/"
    },
    "pricing_url":"https://www.canva.com/pricing/",
    "reddit_query":"Canva Magic Studio pricing review AI features 2025"
  },

  # ── IMAGE GENERATION ─────────────────────────────────────────
  {
    "id":"midjourney","name":"Midjourney","cat":"image","maker":"Midjourney",
    "home":"https://www.midjourney.com/home",
    "sources":{
      "Plans Docs":      "https://docs.midjourney.com/docs/plans",
      "Account":         "https://www.midjourney.com/account",
      "Reddit":          "https://www.reddit.com/r/midjourney/"
    },
    "pricing_url":"https://docs.midjourney.com/docs/plans",
    "reddit_query":"Midjourney pricing plans GPU hours review 2025"
  },
  {
    "id":"dalle","name":"DALL-E","cat":"image","maker":"OpenAI",
    "home":"https://openai.com/index/dall-e-3/",
    "sources":{
      "Product Page":    "https://openai.com/index/dall-e-3/",
      "API Pricing":     "https://openai.com/api/pricing/",
      "ChatGPT Plus":    "https://openai.com/chatgpt/pricing",
      "Reddit":          "https://www.reddit.com/r/dalle/"
    },
    "pricing_url":"https://openai.com/api/pricing/",
    "reddit_query":"DALL-E 3 pricing ChatGPT image generation review 2025"
  },
  {
    "id":"firefly","name":"Adobe Firefly","cat":"image","maker":"Adobe",
    "home":"https://www.adobe.com/in/products/firefly.html",
    "sources":{
      "Product Page":    "https://www.adobe.com/in/products/firefly.html",
      "Pricing":         "https://www.adobe.com/products/firefly/pricing.html",
      "Creative Cloud":  "https://www.adobe.com/creativecloud/plans.html",
      "Reddit":          "https://www.reddit.com/r/Adobe/"
    },
    "pricing_url":"https://www.adobe.com/products/firefly/pricing.html",
    "reddit_query":"Adobe Firefly pricing Creative Cloud review 2025"
  },
  {
    "id":"leonardo","name":"Leonardo AI","cat":"image","maker":"Leonardo AI",
    "home":"https://leonardo.ai/",
    "sources":{
      "Pricing Page":    "https://leonardo.ai/pricing",
      "Features":        "https://leonardo.ai/features",
      "Reddit":          "https://www.reddit.com/r/StableDiffusion/"
    },
    "pricing_url":"https://leonardo.ai/pricing",
    "reddit_query":"Leonardo AI pricing tokens review game dev 2025"
  },

  # ── VIDEO GENERATION ─────────────────────────────────────────
  {
    "id":"runway","name":"Runway","cat":"video","maker":"Runway ML",
    "home":"https://runwayml.com/",
    "sources":{
      "Pricing Page":    "https://runwayml.com/pricing",
      "Research":        "https://runwayml.com/research",
      "Reddit":          "https://www.reddit.com/r/videoproduction/"
    },
    "pricing_url":"https://runwayml.com/pricing",
    "reddit_query":"Runway ML Gen-4 pricing review video generation 2025"
  },
  {
    "id":"synthesia","name":"Synthesia","cat":"video","maker":"Synthesia",
    "home":"https://www.synthesia.io/",
    "sources":{
      "Pricing Page":    "https://www.synthesia.io/pricing",
      "Features":        "https://www.synthesia.io/features",
      "Enterprise":      "https://www.synthesia.io/enterprise",
      "Reddit":          "https://www.reddit.com/r/elearning/"
    },
    "pricing_url":"https://www.synthesia.io/pricing",
    "reddit_query":"Synthesia pricing enterprise avatar video review 2025"
  },
  {
    "id":"pika","name":"Pika","cat":"video","maker":"Pika Labs",
    "home":"https://pikalabs.org/",
    "sources":{
      "Pricing Page":    "https://pika.art/pricing",
      "Features":        "https://pika.art/",
      "Reddit":          "https://www.reddit.com/r/AItools/"
    },
    "pricing_url":"https://pika.art/pricing",
    "reddit_query":"Pika Labs pricing credits video effects review 2025"
  },

  # ── AUDIO & VOICE ────────────────────────────────────────────
  {
    "id":"elevenlabs","name":"ElevenLabs","cat":"audio","maker":"ElevenLabs",
    "home":"https://elevenlabs.io/",
    "sources":{
      "Pricing Page":    "https://elevenlabs.io/pricing",
      "Features":        "https://elevenlabs.io/features",
      "API Docs":        "https://elevenlabs.io/docs",
      "Reddit":          "https://www.reddit.com/r/podcasting/"
    },
    "pricing_url":"https://elevenlabs.io/pricing",
    "reddit_query":"ElevenLabs pricing voice cloning review 2025"
  },
  {
    "id":"murf","name":"Murf","cat":"audio","maker":"Murf AI",
    "home":"https://murf.ai/",
    "sources":{
      "Pricing Page":    "https://murf.ai/pricing",
      "Features":        "https://murf.ai/features",
      "Reddit":          "https://www.reddit.com/r/podcasting/"
    },
    "pricing_url":"https://murf.ai/pricing",
    "reddit_query":"Murf AI pricing voice studio review 2025"
  },
  {
    "id":"descript","name":"Descript","cat":"audio","maker":"Descript",
    "home":"https://www.descript.com/",
    "sources":{
      "Pricing Page":    "https://www.descript.com/pricing",
      "Features":        "https://www.descript.com/features",
      "Reddit":          "https://www.reddit.com/r/podcasting/"
    },
    "pricing_url":"https://www.descript.com/pricing",
    "reddit_query":"Descript Overdub podcast editing pricing review 2025"
  },

  # ── PRODUCTIVITY & AUTOMATION ────────────────────────────────
  {
    "id":"zapier","name":"Zapier AI","cat":"automation","maker":"Zapier",
    "home":"https://zapier.com/ai",
    "sources":{
      "Pricing Page":    "https://zapier.com/pricing",
      "AI Features":     "https://zapier.com/ai",
      "Reddit":          "https://www.reddit.com/r/automation/"
    },
    "pricing_url":"https://zapier.com/pricing",
    "reddit_query":"Zapier AI pricing automation review 2025"
  },
  {
    "id":"make","name":"Make","cat":"automation","maker":"Make",
    "home":"https://www.make.com/en",
    "sources":{
      "Pricing Page":    "https://www.make.com/en/pricing",
      "Features":        "https://www.make.com/en/features",
      "Reddit":          "https://www.reddit.com/r/nocode/"
    },
    "pricing_url":"https://www.make.com/en/pricing",
    "reddit_query":"Make Integromat pricing automation review vs Zapier 2025"
  },
  {
    "id":"agenticworkers","name":"Agentic Workers","cat":"automation","maker":"Agentic Workers",
    "home":"https://www.agenticworkers.com/",
    "sources":{
      "Product Page":    "https://www.agenticworkers.com/",
      "Reddit":          "https://www.reddit.com/r/AItools/"
    },
    "pricing_url":"https://www.agenticworkers.com/",
    "reddit_query":"Agentic Workers AI automation review pricing 2025"
  },
  {
    "id":"manus","name":"Manus","cat":"automation","maker":"Manus AI",
    "home":"https://manus.im/",
    "sources":{
      "Product Page":    "https://manus.im/",
      "Reddit":          "https://www.reddit.com/r/AItools/"
    },
    "pricing_url":"https://manus.im/",
    "reddit_query":"Manus AI autonomous agent pricing review 2025"
  },
  {
    "id":"workbeaver","name":"Workbeaver","cat":"automation","maker":"Workbeaver",
    "home":"https://workbeaver.com/",
    "sources":{
      "Product Page":    "https://workbeaver.com/",
      "Reddit":          "https://www.reddit.com/r/AItools/"
    },
    "pricing_url":"https://workbeaver.com/",
    "reddit_query":"Workbeaver AI automation review pricing 2025"
  },

  # ── PRESENTATION & DOCUMENTS ─────────────────────────────────
  {
    "id":"gamma","name":"Gamma","cat":"gtm","maker":"Gamma Tech",
    "home":"https://gamma.app/",
    "sources":{
      "Pricing Page":    "https://gamma.app/pricing",
      "Features":        "https://gamma.app/features",
      "Reddit":          "https://www.reddit.com/r/productivity/"
    },
    "pricing_url":"https://gamma.app/pricing",
    "reddit_query":"Gamma app presentation pricing review credits 2025"
  },
  {
    "id":"beautifulai","name":"Beautiful.ai","cat":"gtm","maker":"Beautiful.ai",
    "home":"https://www.beautiful.ai/",
    "sources":{
      "Pricing Page":    "https://www.beautiful.ai/pricing",
      "Features":        "https://www.beautiful.ai/features",
      "Reddit":          "https://www.reddit.com/r/productivity/"
    },
    "pricing_url":"https://www.beautiful.ai/pricing",
    "reddit_query":"Beautiful.ai presentation pricing review 2025"
  },
  {
    "id":"tome","name":"Tome","cat":"gtm","maker":"Tome",
    "home":"https://ppt.ai/tome-ai-ppt",
    "sources":{
      "Product Page":    "https://tome.app/",
      "Pricing":         "https://tome.app/pricing",
      "Reddit":          "https://www.reddit.com/r/startups/"
    },
    "pricing_url":"https://tome.app/pricing",
    "reddit_query":"Tome AI presentation tool pricing review 2025"
  },

  # ── DATA & ANALYTICS ─────────────────────────────────────────
  {
    "id":"powerbi","name":"Power BI Copilot","cat":"dashboard","maker":"Microsoft",
    "home":"https://app.powerbi.com/?noSignUpCheck=1",
    "sources":{
      "Pricing Page":    "https://powerbi.microsoft.com/en-us/pricing/",
      "Copilot Docs":    "https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction",
      "Fabric Pricing":  "https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/",
      "Reddit":          "https://www.reddit.com/r/PowerBI/"
    },
    "pricing_url":"https://powerbi.microsoft.com/en-us/pricing/",
    "reddit_query":"Power BI Copilot pricing PPU Fabric review 2025"
  },
  {
    "id":"tableau","name":"Tableau Pulse","cat":"dashboard","maker":"Salesforce",
    "home":"https://www.tableau.com/products/tableau-pulse",
    "sources":{
      "Pricing Page":    "https://www.tableau.com/pricing/teams-orgs",
      "Pulse Product":   "https://www.tableau.com/products/tableau-pulse",
      "Reddit":          "https://www.reddit.com/r/tableau/"
    },
    "pricing_url":"https://www.tableau.com/pricing/teams-orgs",
    "reddit_query":"Tableau Pulse pricing AI review Salesforce 2025"
  },
  {
    "id":"rowsai","name":"Rows AI","cat":"dashboard","maker":"Rows",
    "home":"https://rows.com/ai",
    "sources":{
      "Pricing Page":    "https://rows.com/pricing",
      "AI Features":     "https://rows.com/ai",
      "Reddit":          "https://www.reddit.com/r/analytics/"
    },
    "pricing_url":"https://rows.com/pricing",
    "reddit_query":"Rows AI spreadsheet pricing review 2025"
  },

  # ── APP & WEBSITE BUILDING ───────────────────────────────────
  {
    "id":"lovable","name":"Lovable AI","cat":"webapp","maker":"Lovable",
    "home":"https://lovable.dev/",
    "sources":{
      "Pricing Page":    "https://lovable.dev/pricing",
      "Features":        "https://lovable.dev/features",
      "Reddit":          "https://www.reddit.com/r/vibecoding/"
    },
    "pricing_url":"https://lovable.dev/pricing",
    "reddit_query":"Lovable AI app builder pricing credits review 2025"
  },
]

TOTAL_TOOLS = len(TOOLS)  # 50

# ── HTML TEXT EXTRACTOR ──────────────────────────────────────────
class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags  = {'script','style','nav','footer','head','noscript'}
        self.skip       = 0

    def handle_starttag(self, tag, attrs):
        if tag in self.skip_tags:
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in self.skip_tags and self.skip > 0:
            self.skip -= 1

    def handle_data(self, data):
        if self.skip == 0:
            stripped = data.strip()
            if len(stripped) > 2:
                self.text_parts.append(stripped)

    def get_text(self):
        return ' '.join(self.text_parts)


def scrape_page(url: str, max_chars: int = 6000) -> str:
    """Fetch a web page and return clean text, truncated to max_chars."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        r.raise_for_status()
        parser = TextExtractor()
        parser.feed(r.text)
        text = parser.get_text()
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        print(f"    Scrape failed for {url}: {e}")
        return ""


def fetch_reddit(query: str, limit: int = 5) -> list:
    """Fetch top Reddit posts/comments for a query. Returns list of quote strings."""
    try:
        url = f"https://www.reddit.com/search.json?q={requests.utils.quote(query)}&sort=relevance&t=month&limit={limit}&type=link"
        r = requests.get(url, headers={
            "User-Agent": "AI-Tools-Dashboard-Bot/1.0 (monitoring tool)"
        }, timeout=15)
        r.raise_for_status()
        data   = r.json()
        posts  = data.get("data", {}).get("children", [])
        quotes = []
        for post in posts:
            pd    = post.get("data", {})
            title = pd.get("title", "").strip()
            body  = pd.get("selftext", "").strip()
            sub   = pd.get("subreddit", "")
            score = pd.get("score", 0)
            if score < 5:
                continue
            text = body if len(body) > 30 else title
            if len(text) > 20:
                # Trim to readable length
                text = text[:200].rstrip() + ("..." if len(text) > 200 else "")
                quotes.append(f'"{text}" — r/{sub}')
            if len(quotes) >= 3:
                break
        return quotes
    except Exception as e:
        print(f"    Reddit fetch failed: {e}")
        return []


# ── NVIDIA API ───────────────────────────────────────────────────
def ask_nvidia(system_msg: str, user_msg: str, retries: int = 3) -> str | None:
    """Call NVIDIA NIM API and return response text."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type":  "application/json"
    }
    body = {
        "model":       NVIDIA_MODEL,
        "messages":    [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        "temperature": 0.05,
        "max_tokens":  900,
        "top_p":       0.9
    }
    for attempt in range(retries):
        try:
            r = requests.post(NVIDIA_URL, headers=headers, json=body, timeout=35)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            print(f"    HTTP {code} attempt {attempt+1}/{retries}")
            if code in [401, 403]:
                print("    Auth error — check NVIDIA API key")
                return None
            if code == 429:
                wait = (attempt + 1) * 15
                print(f"    Rate limited — waiting {wait}s")
                time.sleep(wait)
            else:
                time.sleep(4)
        except Exception as e:
            print(f"    API error attempt {attempt+1}: {e}")
            time.sleep(4)
    return None


def safe_json(text: str):
    """Safely parse JSON from model response."""
    if not text:
        return None
    t = text.strip()
    # Strip markdown code fences
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.MULTILINE)
    t = re.sub(r'```\s*$', '', t, flags=re.MULTILINE)
    t = t.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    # Try extracting first array or object
    for pat in [r'(\[[\s\S]*?\])', r'(\{[\s\S]*?\})']:
        m = re.search(pat, t)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                pass
    return None


# ── PER-TOOL DATA EXTRACTION ─────────────────────────────────────
SYS = ("You are a precise AI tool researcher. "
       "Return ONLY valid JSON with no markdown, no code fences, no extra text. "
       "If unsure of a value use null.")


def extract_pricing(tool_name: str, page_text: str) -> list:
    """Extract all pricing plans from scraped page text."""
    if not page_text:
        return []
    prompt = f"""From this official pricing page content for {tool_name}, extract EVERY pricing plan.
Do NOT miss any plan. Include free tiers, trial periods, all paid tiers, enterprise tiers.

Page content:
{page_text}

Return ONLY this JSON array — no other text:
[
  {{"name":"Plan Name","price":"$X/month","billing":"monthly|annual|custom","description":"what is included in this plan"}}
]
If price is custom or contact sales, use "Custom — contact sales" as the price value.
Include all plans found. If billed annually show both monthly equivalent and annual total."""

    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list):
        return parsed
    return []


def extract_features(tool_name: str, page_text: str) -> list:
    """Extract key features from page text."""
    if not page_text:
        return []
    prompt = f"""From this official product page content for {tool_name}, list the TOP 10 KEY FEATURES.

Page content:
{page_text}

Return ONLY a JSON array of feature strings — no other text:
["Feature 1","Feature 2","Feature 3"]"""
    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list):
        return parsed[:12]
    return []


def extract_free_limits(tool_name: str, page_text: str) -> list:
    """Extract free plan limitations from page text."""
    if not page_text:
        return []
    prompt = f"""From this official pricing page for {tool_name}, list ALL FREE PLAN LIMITATIONS.
Include: message limits, feature restrictions, storage caps, no X features, trial periods, watermarks, etc.

Page content:
{page_text}

Return ONLY a JSON array of limitation strings — no other text:
["Limitation 1","Limitation 2","Limitation 3"]
If there is no free plan at all, return: ["No free plan available — paid subscription required"]"""
    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list):
        return parsed
    return []


def extract_limits(tool_name: str, page_text: str) -> dict:
    """Extract usage limits and caps from page text."""
    if not page_text:
        return {}
    prompt = f"""From this official page for {tool_name}, extract all USAGE LIMITS AND CAPS.
Include: context window, message/query daily cap, file upload limit, storage, API rate limits, seat minimums, token limits.

Page content:
{page_text}

Return ONLY a JSON object — no other text:
{{"Context window":"value","Daily message cap":"value","File upload limit":"value","API rate limit":"value"}}
Use "Not specified" for limits not mentioned."""
    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, dict):
        return {k: v for k, v in parsed.items() if v and v != "null"}
    return {}


def research_pros_cons(tool_name: str) -> dict:
    """Use NVIDIA API to research pros and cons from general knowledge."""
    prompt = f"""Research the pros, cons, and hidden limitations of {tool_name} AI tool as of 2025.
Focus on real user pain points, hidden costs, and commonly reported issues.

Return ONLY this JSON structure — no other text:
{{
  "pros": ["Top advantage 1","Advantage 2","Advantage 3","Advantage 4","Advantage 5"],
  "cons": ["Key limitation or hidden cost 1","User complaint 2","Hidden issue 3","Limitation 4","Limitation 5"]
}}"""
    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, dict) and "pros" in parsed and "cons" in parsed:
        return parsed
    return {"pros": [], "cons": []}


def research_use_cases(tool_name: str) -> list:
    """Research primary use cases for the tool."""
    prompt = f"""List the TOP 8 PRIMARY USE CASES for {tool_name} AI tool as of 2025.
Be specific and practical — what do real users actually use it for daily?

Return ONLY a JSON array — no other text:
["Use case 1","Use case 2","Use case 3"]"""
    raw    = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list):
        return parsed[:10]
    return []


# ── CACHE ────────────────────────────────────────────────────────
def load_cache() -> dict:
    if os.path.exists("cache.json"):
        try:
            with open("cache.json") as f:
                return json.load(f)
        except:
            pass
    return {}


def save_cache(data: dict) -> None:
    with open("cache.json", "w") as f:
        json.dump(data, f, indent=2)


# ── CHANGE DETECTION ─────────────────────────────────────────────
def detect_changes(tid: str, section: str, new_data, old_cache: dict) -> list:
    if tid not in old_cache or section not in old_cache[tid]:
        return []
    old_str = json.dumps(old_cache[tid].get(section, ""), sort_keys=True)
    new_str = json.dumps(new_data, sort_keys=True)
    if old_str == new_str:
        return []

    changes = []
    old_prices = set(re.findall(r'\$[\d,]+(?:\.\d+)?(?:/\w+)?', old_str))
    new_prices  = set(re.findall(r'\$[\d,]+(?:\.\d+)?(?:/\w+)?', new_str))
    added   = new_prices - old_prices
    removed = old_prices - new_prices
    if added:
        changes.append(f"{section}: new prices — {', '.join(sorted(added))}")
    if removed:
        changes.append(f"{section}: removed — {', '.join(sorted(removed))}")
    if not changes:
        changes.append(f"{section}: content updated")
    return changes


# ── HTML BANNER UPDATE ───────────────────────────────────────────
def update_html_banner(html: str, changes_count: int) -> str:
    """Update only the auto-banner div in index.html with IST timestamp."""
    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    banner = (
        f'<div id="auto-banner" style="background:#f0fdf4;border:1px solid #86efac;'
        f'border-radius:8px;padding:10px 16px;margin-bottom:14px;font-size:12px;'
        f'color:#166534;font-family:Inter,sans-serif;display:flex;gap:16px;flex-wrap:wrap;align-items:center;">'
        f'&#x1F504; <strong>Auto-updated:</strong> {now_ist} &nbsp;|&nbsp; '
        f'<strong>Changes today:</strong> {changes_count} &nbsp;|&nbsp; '
        f'<strong>Tools tracked:</strong> {TOTAL_TOOLS} &nbsp;|&nbsp; '
        f'<strong>Sections per tool:</strong> 7'
        f'</div>'
    )
    # Remove existing banner if present
    html = re.sub(r'<div id="auto-banner"[\s\S]*?</div>', '', html, count=1)
    # Insert before stat-row
    html = html.replace('<div class="stat-row">', banner + '\n  <div class="stat-row">', 1)
    return html


# ── WRITE DATA.JSON ──────────────────────────────────────────────
def write_data_json(all_tool_data: dict, changes_count: int) -> None:
    """Write data.json that index.html fetches to update itself."""
    now_ist = datetime.now(IST).strftime("%d %b %Y, %I:%M %p IST")
    output = {
        "meta": {
            "updated":  now_ist,
            "total":    TOTAL_TOOLS,
            "changes":  changes_count,
            "sections": 7
        },
        "tools": all_tool_data
    }
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"data.json written ✓  ({TOTAL_TOOLS} tools, {changes_count} changes)")


# ── TELEGRAM ─────────────────────────────────────────────────────
def telegram(msg: str) -> None:
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg[:4000], "parse_mode": "HTML"},
            timeout=12
        )
        print("Telegram sent ✓")
    except Exception as e:
        print(f"Telegram failed: {e}")


# ── MAIN ─────────────────────────────────────────────────────────
def main():
    now_ist = datetime.now(IST).strftime("%Y-%m-%d %H:%M IST")
    print(f"\n{'='*65}")
    print(f"  AI Tools Dashboard Auto-Update")
    print(f"  Time    : {now_ist}")
    print(f"  Model   : {NVIDIA_MODEL}")
    print(f"  Tools   : {TOTAL_TOOLS}")
    print(f"{'='*65}\n")

    if not os.path.exists("index.html"):
        msg = "⚠️ <b>Update Failed</b>\nindex.html not found."
        print(msg)
        telegram(msg)
        return

    old_cache    = load_cache()
    new_cache    = {}
    all_tool_data = {}
    all_changes  = []

    for idx, tool in enumerate(TOOLS, 1):
        tid   = tool["id"]
        tname = tool["name"]
        purl  = tool["pricing_url"]
        rq    = tool["reddit_query"]
        srcs  = tool["sources"]

        print(f"\n[{idx:02d}/{TOTAL_TOOLS}]  {tname}")
        new_cache[tid] = {"name": tname, "updated": datetime.now(IST).isoformat()}
        tool_data      = {"sources": srcs}
        tool_changes   = []

        # 1) Scrape official pricing page
        print(f"  Scraping: {purl}")
        page_text = scrape_page(purl)
        time.sleep(1.5)

        # 2) Extract pricing plans
        print(f"  → pricing plans ...", end=" ", flush=True)
        plans = extract_pricing(tname, page_text)
        if plans:
            print(f"✓  ({len(plans)} plans)")
            tool_data["plans"] = plans
            new_cache[tid]["plans"] = plans
            changes = detect_changes(tid, "plans", plans, old_cache)
            tool_changes.extend(changes)
        else:
            print("✗  (using cached)")
            if tid in old_cache and "plans" in old_cache[tid]:
                tool_data["plans"] = old_cache[tid]["plans"]
        time.sleep(2)

        # 3) Extract free limits
        print(f"  → free limits    ...", end=" ", flush=True)
        free = extract_free_limits(tname, page_text)
        if free:
            print(f"✓  ({len(free)} items)")
            tool_data["free"] = free
            new_cache[tid]["free"] = free
        else:
            print("✗  (using cached)")
            if tid in old_cache and "free" in old_cache[tid]:
                tool_data["free"] = old_cache[tid]["free"]
        time.sleep(2)

        # 4) Extract usage limits
        print(f"  → usage limits   ...", end=" ", flush=True)
        limits = extract_limits(tname, page_text)
        if limits:
            print(f"✓  ({len(limits)} items)")
            tool_data["limits"] = limits
            new_cache[tid]["limits"] = limits
            changes = detect_changes(tid, "limits", limits, old_cache)
            tool_changes.extend(changes)
        else:
            print("✗  (using cached)")
            if tid in old_cache and "limits" in old_cache[tid]:
                tool_data["limits"] = old_cache[tid]["limits"]
        time.sleep(2)

        # 5) Extract features (try to scrape home page for feature info)
        print(f"  → features       ...", end=" ", flush=True)
        feat_text = page_text  # reuse pricing page; often has features too
        feats = extract_features(tname, feat_text)
        if feats:
            print(f"✓  ({len(feats)} features)")
            tool_data["feats"] = feats
            new_cache[tid]["feats"] = feats
        else:
            print("✗  (using cached)")
            if tid in old_cache and "feats" in old_cache[tid]:
                tool_data["feats"] = old_cache[tid]["feats"]
        time.sleep(2)

        # 6) Pros / Cons — NVIDIA API knowledge-based
        print(f"  → pros & cons    ...", end=" ", flush=True)
        pc = research_pros_cons(tname)
        if pc.get("pros") or pc.get("cons"):
            print(f"✓")
            tool_data["pros"] = pc.get("pros", [])
            tool_data["cons"] = pc.get("cons", [])
            new_cache[tid]["pros"] = tool_data["pros"]
            new_cache[tid]["cons"] = tool_data["cons"]
        else:
            print("✗  (using cached)")
            if tid in old_cache:
                if "pros" in old_cache[tid]: tool_data["pros"] = old_cache[tid]["pros"]
                if "cons" in old_cache[tid]: tool_data["cons"] = old_cache[tid]["cons"]
        time.sleep(2)

        # 7) Reddit community feedback
        print(f"  → reddit         ...", end=" ", flush=True)
        reddit_quotes = fetch_reddit(rq)
        if reddit_quotes:
            print(f"✓  ({len(reddit_quotes)} quotes)")
            tool_data["reddit"] = reddit_quotes
            new_cache[tid]["reddit"] = reddit_quotes
            changes = detect_changes(tid, "reddit", reddit_quotes, old_cache)
            tool_changes.extend(changes)
        else:
            print("✗  (using cached)")
            if tid in old_cache and "reddit" in old_cache[tid]:
                tool_data["reddit"] = old_cache[tid]["reddit"]
        time.sleep(2)

        # 8) Use cases
        if tid not in old_cache or "uses" not in old_cache[tid]:
            print(f"  → use cases      ...", end=" ", flush=True)
            uses = research_use_cases(tname)
            if uses:
                print(f"✓  ({len(uses)} items)")
                tool_data["uses"] = uses
                new_cache[tid]["uses"] = uses
            else:
                print("✗")
            time.sleep(2)
        else:
            tool_data["uses"] = old_cache[tid]["uses"]

        # Store tool data
        all_tool_data[tid] = tool_data

        if tool_changes:
            all_changes.append({"tool": tname, "changes": tool_changes})
            print(f"  ⚡  {len(tool_changes)} changes detected")

    # Save cache
    save_cache(new_cache)

    # Write data.json
    write_data_json(all_tool_data, len(all_changes))

    # Update index.html banner only
    with open("index.html", encoding="utf-8") as f:
        html = f.read()
    html = update_html_banner(html, len(all_changes))
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html banner updated ✓")

    # Send Telegram notification
    today = datetime.now(IST).strftime("%d %b %Y")

    if all_changes:
        by_cat: dict = {}
        for item in all_changes:
            # find category
            cat = next((t["cat"] for t in TOOLS if t["name"] == item["tool"]), "other")
            by_cat.setdefault(cat, []).append(item)

        lines = [f"<b>&#x1F6A8; AI Tools Update — {today} (IST)</b>"]
        lines.append(f"<b>{len(all_changes)} tool(s) updated</b>\n")
        for cat, items in by_cat.items():
            lines.append(f"\n<b>&#x1F4CC; {cat.upper()}</b>")
            for item in items:
                lines.append(f"  &#x1F504; <b>{item['tool']}</b>")
                for c in item["changes"][:3]:
                    lines.append(f"    • {c}")
        lines.append(
            f"\n\n&#x1F4CA; https://{GITHUB_USER}.github.io/ai-tools-dashboard"
        )
        telegram("\n".join(lines))
    else:
        telegram(
            f"&#x2705; <b>Daily Check Complete — {today} (IST)</b>\n\n"
            f"All <b>{TOTAL_TOOLS} tools</b> checked across 7 sections each.\n"
            f"No pricing or feature changes detected today.\n\n"
            f"&#x1F4CA; https://{GITHUB_USER}.github.io/ai-tools-dashboard"
        )

    print(f"\n{'='*65}")
    print(f"  Done — {len(all_changes)} tools changed")
    print(f"  Completed: {datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}")
    print(f"{'='*65}\n")


if __name__ == "__main__":
    main()
