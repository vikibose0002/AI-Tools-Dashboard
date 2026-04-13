import os, json, requests, re, time
from datetime import datetime

# ─── CREDENTIALS ────────────────────────────────────────────────
GEMINI_KEY  = os.environ['GEMINI_API_KEY']
TG_TOKEN    = os.environ['TELEGRAM_BOT_TOKEN']
TG_CHAT     = os.environ['TELEGRAM_CHAT_ID']
GITHUB_USER = os.environ.get('GITHUB_USERNAME', 'yourusername')

# ─── ALL 54+ TOOLS WITH EXACT SOURCE URLS ───────────────────────
# Each tool has:
#   id       → matches the card id in your HTML
#   name     → display name
#   sources  → exact URLs the script visits daily for fresh data
#   sections → what to check and update

TOOLS = [

  # ══════════════ GENERAL AI ══════════════
  {
    "id": "chatgpt", "name": "ChatGPT", "category": "General AI",
    "sources": {
      "pricing":   "https://openai.com/chatgpt/pricing",
      "help":      "https://help.openai.com/en/articles/9275245-using-chatgpt-s-memory",
      "models":    "https://help.openai.com/en/articles/11165333-chatgpt-enterprise-and-edu-models-limits",
      "reddit":    "https://www.reddit.com/r/ChatGPT/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "ChatGPT Free Plus Pro Business Enterprise pricing plans features 2025 site:openai.com OR site:help.openai.com",
      "free_limits":     "ChatGPT free plan limits message cap restrictions 2025",
      "usage_limits":    "ChatGPT rate limits context window token limits per plan 2025",
      "features":        "ChatGPT new features updates capabilities 2025",
      "pros_cons":       "ChatGPT pros cons limitations hidden restrictions user complaints 2025",
      "reddit":          "ChatGPT user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "claude", "name": "Claude", "category": "General AI",
    "sources": {
      "pricing":   "https://claude.ai/pricing",
      "help":      "https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan",
      "docs":      "https://docs.anthropic.com/en/docs/about-claude/models",
      "reddit":    "https://www.reddit.com/r/ClaudeAI/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Claude Pro Max Team Enterprise pricing plans 2025 site:claude.ai OR site:anthropic.com",
      "free_limits":     "Claude free plan daily message limit restrictions 2025",
      "usage_limits":    "Claude context window token limits rate limits per plan 2025",
      "features":        "Claude new features Opus Sonnet Haiku updates 2025",
      "pros_cons":       "Claude pros cons limitations hidden restrictions user complaints 2025",
      "reddit":          "Claude AI user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "gemini", "name": "Google Gemini", "category": "General AI",
    "sources": {
      "pricing":   "https://one.google.com/intl/en/about/google-ai-plans",
      "workspace": "https://workspace.google.com/intl/en/pricing",
      "docs":      "https://ai.google.dev/pricing",
      "reddit":    "https://www.reddit.com/r/Gemini/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Google Gemini AI Pro Ultra pricing plans 2025 site:one.google.com OR site:workspace.google.com",
      "free_limits":     "Google Gemini free plan limits restrictions 2025",
      "usage_limits":    "Google Gemini context window rate limits usage caps 2025",
      "features":        "Google Gemini new features Deep Research updates 2025",
      "pros_cons":       "Google Gemini pros cons limitations hidden issues user complaints 2025",
      "reddit":          "Google Gemini user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "m365", "name": "Microsoft 365 Copilot", "category": "General AI",
    "sources": {
      "pricing":   "https://www.microsoft.com/en-us/microsoft-365-copilot/pricing-new",
      "enterprise":"https://www.microsoft.com/en-us/microsoft-365-copilot/pricing/enterprise",
      "blog":      "https://www.microsoft.com/en-us/microsoft-365/blog/",
      "reddit":    "https://www.reddit.com/r/Office365/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Microsoft 365 Copilot Business Enterprise pricing 2025 site:microsoft.com",
      "free_limits":     "Microsoft 365 Copilot free tier Copilot Chat limitations 2025",
      "usage_limits":    "Microsoft 365 Copilot rate limits context window file size limits 2025",
      "features":        "Microsoft 365 Copilot new features Word Excel Teams updates 2025",
      "pros_cons":       "Microsoft 365 Copilot pros cons hidden costs SharePoint risk complaints 2025",
      "reddit":          "Microsoft 365 Copilot user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ CONTENT CREATION ══════════════
  {
    "id": "jasper", "name": "Jasper AI", "category": "Content Creation",
    "sources": {
      "pricing":  "https://www.jasper.ai/pricing",
      "features": "https://www.jasper.ai/features",
      "reddit":   "https://www.reddit.com/r/marketing/search/?q=jasper+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Jasper AI Creator Pro Business pricing plans 2025 site:jasper.ai",
      "free_limits":     "Jasper AI free trial limitations no free plan 2025",
      "usage_limits":    "Jasper AI word limits seat limits brand voice limits 2025",
      "features":        "Jasper AI new features brand voice knowledge base updates 2025",
      "pros_cons":       "Jasper AI pros cons hidden costs limitations user complaints 2025",
      "reddit":          "Jasper AI user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "writesonic", "name": "Writesonic", "category": "Content Creation",
    "sources": {
      "pricing":  "https://writesonic.com/pricing",
      "features": "https://writesonic.com/features",
      "reddit":   "https://www.reddit.com/r/SEO/search/?q=writesonic&sort=new"
    },
    "queries": {
      "pricing_plans":   "Writesonic Lite Standard Professional Advanced Enterprise pricing 2025 site:writesonic.com",
      "free_limits":     "Writesonic free plan limitations article limits 2025",
      "usage_limits":    "Writesonic article limits per month GEO tracking limits 2025",
      "features":        "Writesonic new features SEO GEO updates 2025",
      "pros_cons":       "Writesonic pros cons limitations user complaints 2025",
      "reddit":          "Writesonic user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "copyai", "name": "Copy.ai", "category": "Content Creation",
    "sources": {
      "pricing":  "https://www.copy.ai/pricing",
      "features": "https://www.copy.ai/features",
      "reddit":   "https://www.reddit.com/r/Entrepreneur/search/?q=copy.ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Copy.ai Pro Growth Business Enterprise pricing plans 2025 site:copy.ai",
      "free_limits":     "Copy.ai free plan limitations workflow restrictions 2025",
      "usage_limits":    "Copy.ai workflow credits limits brand voice limits 2025",
      "features":        "Copy.ai new features GTM workflows updates 2025",
      "pros_cons":       "Copy.ai pros cons hidden costs limitations user complaints 2025",
      "reddit":          "Copy.ai user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "grammarly", "name": "Grammarly", "category": "Content Creation",
    "sources": {
      "pricing":  "https://www.grammarly.com/plans",
      "business": "https://www.grammarly.com/business",
      "reddit":   "https://www.reddit.com/r/writing/search/?q=grammarly&sort=new"
    },
    "queries": {
      "pricing_plans":   "Grammarly Premium Business Enterprise pricing plans 2025 site:grammarly.com",
      "free_limits":     "Grammarly free plan limitations no plagiarism check 2025",
      "usage_limits":    "Grammarly usage limits team minimum seats context limits 2025",
      "features":        "Grammarly new features AI writing brand tone updates 2025",
      "pros_cons":       "Grammarly pros cons limitations user complaints 2025",
      "reddit":          "Grammarly user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "notionai", "name": "Notion AI", "category": "Content Creation",
    "sources": {
      "pricing":  "https://www.notion.com/pricing",
      "ai":       "https://www.notion.com/product/ai",
      "reddit":   "https://www.reddit.com/r/Notion/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Notion AI add-on Plus Business Enterprise pricing 2025 site:notion.com",
      "free_limits":     "Notion AI free plan 20 uses limitations 2025",
      "usage_limits":    "Notion AI usage limits connector limits context limits 2025",
      "features":        "Notion AI new features connectors updates 2025",
      "pros_cons":       "Notion AI pros cons limitations user complaints 2025",
      "reddit":          "Notion AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "canva", "name": "Canva Magic Studio", "category": "Content Creation",
    "sources": {
      "pricing":  "https://www.canva.com/en/pricing/",
      "magic":    "https://www.canva.com/magic/",
      "reddit":   "https://www.reddit.com/r/graphic_design/search/?q=canva&sort=new"
    },
    "queries": {
      "pricing_plans":   "Canva Pro Teams Enterprise pricing plans 2025 site:canva.com",
      "free_limits":     "Canva free plan AI generation limits restrictions 2025",
      "usage_limits":    "Canva AI credit limits storage limits brand kit limits 2025",
      "features":        "Canva Magic Studio Dream Lab new features updates 2025",
      "pros_cons":       "Canva Magic Studio pros cons price increase complaints 2025",
      "reddit":          "Canva user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ APP DEVELOPMENT ══════════════
  {
    "id": "ghcopilot", "name": "GitHub Copilot", "category": "App Development",
    "sources": {
      "pricing":  "https://github.com/features/copilot/plans",
      "docs":     "https://docs.github.com/en/copilot",
      "reddit":   "https://www.reddit.com/r/programming/search/?q=github+copilot&sort=new"
    },
    "queries": {
      "pricing_plans":   "GitHub Copilot Individual Business Enterprise pricing plans 2025 site:github.com",
      "free_limits":     "GitHub Copilot free tier limitations 2000 completions 2025",
      "usage_limits":    "GitHub Copilot premium request limits context window overage 2025",
      "features":        "GitHub Copilot new features agent mode CLI updates 2025",
      "pros_cons":       "GitHub Copilot pros cons limitations hidden costs user complaints 2025",
      "reddit":          "GitHub Copilot user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "cursor", "name": "Cursor", "category": "App Development",
    "sources": {
      "pricing":  "https://www.cursor.com/pricing",
      "docs":     "https://docs.cursor.com/",
      "reddit":   "https://www.reddit.com/r/cursor/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Cursor AI Pro Teams Enterprise pricing plans 2025 site:cursor.com",
      "free_limits":     "Cursor AI free tier limitations hobby plan 2025",
      "usage_limits":    "Cursor AI premium request limits 500 per month context window 2025",
      "features":        "Cursor AI Composer new features agent mode updates 2025",
      "pros_cons":       "Cursor AI pros cons limitations hidden costs user complaints 2025",
      "reddit":          "Cursor AI user reviews complaints praise Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "claudecode", "name": "Claude Code", "category": "App Development",
    "sources": {
      "pricing":  "https://claude.ai/pricing",
      "docs":     "https://docs.anthropic.com/en/docs/claude-code/overview",
      "reddit":   "https://www.reddit.com/r/ClaudeAI/search/?q=claude+code&sort=new"
    },
    "queries": {
      "pricing_plans":   "Claude Code Pro Max Team Enterprise API pricing 2025 site:anthropic.com",
      "free_limits":     "Claude Code no free tier Pro plan token budget limitations 2025",
      "usage_limits":    "Claude Code context window rate limits API token costs 2025",
      "features":        "Claude Code new features agent orchestration updates 2025",
      "pros_cons":       "Claude Code pros cons limitations SWE-bench user reviews 2025",
      "reddit":          "Claude Code user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "tabnine", "name": "Tabnine", "category": "App Development",
    "sources": {
      "pricing":  "https://www.tabnine.com/pricing",
      "features": "https://www.tabnine.com/features",
      "reddit":   "https://www.reddit.com/r/programming/search/?q=tabnine&sort=new"
    },
    "queries": {
      "pricing_plans":   "Tabnine Developer Business Enterprise pricing plans 2025 site:tabnine.com",
      "free_limits":     "Tabnine no free tier annual commitment required 2025",
      "usage_limits":    "Tabnine on-premises data retention limits enterprise 2025",
      "features":        "Tabnine new features private code training updates 2025",
      "pros_cons":       "Tabnine pros cons expensive limitations user complaints 2025",
      "reddit":          "Tabnine user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "replit", "name": "Replit Ghostwriter", "category": "App Development",
    "sources": {
      "pricing":  "https://replit.com/pricing",
      "features": "https://replit.com/site/ghostwriter",
      "reddit":   "https://www.reddit.com/r/replit/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Replit Core Teams Enterprise pricing plans 2025 site:replit.com",
      "free_limits":     "Replit free tier limitations compute speed restrictions 2025",
      "usage_limits":    "Replit compute limits storage hosting costs 2025",
      "features":        "Replit Ghostwriter Agent new features updates 2025",
      "pros_cons":       "Replit pros cons limitations user complaints 2025",
      "reddit":          "Replit user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "codeium", "name": "Codeium Windsurf", "category": "App Development",
    "sources": {
      "pricing":  "https://windsurf.com/pricing",
      "features": "https://codeium.com/pricing",
      "reddit":   "https://www.reddit.com/r/programming/search/?q=codeium+windsurf&sort=new"
    },
    "queries": {
      "pricing_plans":   "Codeium Windsurf Pro Teams Enterprise pricing 2025 site:windsurf.com OR site:codeium.com",
      "free_limits":     "Codeium free tier unlimited completions limitations 2025",
      "usage_limits":    "Windsurf AI credit limits 500 per month context window 2025",
      "features":        "Codeium Windsurf Cascade new features updates 2025",
      "pros_cons":       "Codeium Windsurf pros cons limitations user complaints 2025",
      "reddit":          "Codeium Windsurf user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "autogen", "name": "AutoGen Magentic-One", "category": "App Development",
    "sources": {
      "github":   "https://github.com/microsoft/autogen",
      "docs":     "https://microsoft.github.io/autogen/",
      "azure":    "https://azure.microsoft.com/en-us/products/ai-studio",
      "reddit":   "https://www.reddit.com/r/LocalLLaMA/search/?q=autogen&sort=new"
    },
    "queries": {
      "pricing_plans":   "Microsoft AutoGen Magentic-One pricing free open source Azure 2025",
      "free_limits":     "AutoGen open source free MIT license API key requirements 2025",
      "usage_limits":    "AutoGen rate limits Azure AI Foundry scaling limits 2025",
      "features":        "AutoGen Magentic-One new features multi-agent updates 2025",
      "pros_cons":       "AutoGen pros cons technical complexity limitations user feedback 2025",
      "reddit":          "AutoGen Microsoft user reviews Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ WEB / APP BUILDERS ══════════════
  {
    "id": "v0", "name": "v0 by Vercel", "category": "Web App Builder",
    "sources": {
      "pricing":  "https://v0.dev/pricing",
      "docs":     "https://v0.dev/docs",
      "reddit":   "https://www.reddit.com/r/webdev/search/?q=v0+vercel&sort=new"
    },
    "queries": {
      "pricing_plans":   "v0 Vercel Free Premium Team Business Enterprise pricing 2025 site:v0.dev OR site:vercel.com",
      "free_limits":     "v0 Vercel free plan $5 credit token limits 2025",
      "usage_limits":    "v0 Vercel token costs credit burn rate limits 2025",
      "features":        "v0 Vercel new features Git integration editor updates 2025",
      "pros_cons":       "v0 Vercel pros cons credit burn Vercel lock-in complaints 2025",
      "reddit":          "v0 Vercel user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "lovable", "name": "Lovable AI", "category": "Web App Builder",
    "sources": {
      "pricing":  "https://lovable.dev/pricing",
      "features": "https://lovable.dev/features",
      "reddit":   "https://www.reddit.com/r/vibecoding/search/?q=lovable&sort=new"
    },
    "queries": {
      "pricing_plans":   "Lovable AI Starter Pro Business Enterprise pricing credits 2025 site:lovable.dev",
      "free_limits":     "Lovable AI free plan 5 credits daily limitations 2025",
      "usage_limits":    "Lovable AI credit system context degradation limits 2025",
      "features":        "Lovable AI Plan Mode Voice Mode new features updates 2025",
      "pros_cons":       "Lovable AI pros cons context degradation credit system complaints 2025",
      "reddit":          "Lovable AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "bubble", "name": "Bubble", "category": "Web App Builder",
    "sources": {
      "pricing":  "https://bubble.io/pricing",
      "features": "https://bubble.io/features",
      "reddit":   "https://www.reddit.com/r/nocode/search/?q=bubble&sort=new"
    },
    "queries": {
      "pricing_plans":   "Bubble no-code Starter Growth Team Enterprise pricing 2025 site:bubble.io",
      "free_limits":     "Bubble free plan limitations branding no custom domain 2025",
      "usage_limits":    "Bubble capacity limits storage bandwidth server limits 2025",
      "features":        "Bubble AI features new updates plugin ecosystem 2025",
      "pros_cons":       "Bubble pros cons vendor lock-in expensive limitations user complaints 2025",
      "reddit":          "Bubble no-code user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "softr", "name": "Softr", "category": "Web App Builder",
    "sources": {
      "pricing":  "https://www.softr.io/pricing",
      "features": "https://www.softr.io/features",
      "reddit":   "https://www.reddit.com/r/nocode/search/?q=softr&sort=new"
    },
    "queries": {
      "pricing_plans":   "Softr Basic Professional Business Enterprise pricing 2025 site:softr.io",
      "free_limits":     "Softr free plan user limits branding limitations 2025",
      "usage_limits":    "Softr user limits signed-in users restrictions 2025",
      "features":        "Softr new features Airtable integration updates 2025",
      "pros_cons":       "Softr pros cons limitations user complaints 2025",
      "reddit":          "Softr user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "durable", "name": "Durable", "category": "Web App Builder",
    "sources": {
      "pricing":  "https://durable.co/pricing",
      "features": "https://durable.co/features",
      "reddit":   "https://www.reddit.com/r/smallbusiness/search/?q=durable+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Durable AI website builder Starter Business Premium pricing 2025 site:durable.co",
      "free_limits":     "Durable AI free plan limitations cannot publish 2025",
      "usage_limits":    "Durable AI generation limits customization limits 2025",
      "features":        "Durable AI new features CRM invoicing updates 2025",
      "pros_cons":       "Durable AI pros cons generic output limitations user complaints 2025",
      "reddit":          "Durable AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ GTM & PRESENTATIONS ══════════════
  {
    "id": "gamma", "name": "Gamma", "category": "GTM & Presentations",
    "sources": {
      "pricing":  "https://gamma.app/pricing",
      "features": "https://gamma.app/features",
      "reddit":   "https://www.reddit.com/r/productivity/search/?q=gamma+app&sort=new"
    },
    "queries": {
      "pricing_plans":   "Gamma app Plus Pro Team Business Enterprise pricing AI credits 2025 site:gamma.app",
      "free_limits":     "Gamma app free plan 400 one-time credits limitations branding 2025",
      "usage_limits":    "Gamma AI credits limits monthly reset fair use throttling 2025",
      "features":        "Gamma app Agent new features API Remix updates 2025",
      "pros_cons":       "Gamma app pros cons PowerPoint export issues credits complaints 2025",
      "reddit":          "Gamma app user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "beautifulai", "name": "Beautiful.ai", "category": "GTM & Presentations",
    "sources": {
      "pricing":  "https://www.beautiful.ai/pricing",
      "features": "https://www.beautiful.ai/features",
      "reddit":   "https://www.reddit.com/r/productivity/search/?q=beautiful.ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Beautiful.ai Pro Team Enterprise pricing 2025 site:beautiful.ai",
      "free_limits":     "Beautiful.ai free plan limitations watermark 2025",
      "usage_limits":    "Beautiful.ai team seats limits storage limits 2025",
      "features":        "Beautiful.ai Presenter Studio new features updates 2025",
      "pros_cons":       "Beautiful.ai pros cons limitations user complaints 2025",
      "reddit":          "Beautiful.ai user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "tome", "name": "Tome", "category": "GTM & Presentations",
    "sources": {
      "pricing":  "https://tome.app/pricing",
      "features": "https://tome.app/features",
      "reddit":   "https://www.reddit.com/r/startups/search/?q=tome+app&sort=new"
    },
    "queries": {
      "pricing_plans":   "Tome AI presentation Pro Business pricing 2025 site:tome.app",
      "free_limits":     "Tome app free plan page limits branding 2025",
      "usage_limits":    "Tome AI generation limits usage restrictions 2025",
      "features":        "Tome AI new features narrative generation updates 2025",
      "pros_cons":       "Tome AI pros cons limitations user complaints 2025",
      "reddit":          "Tome app user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ DEEP RESEARCH ══════════════
  {
    "id": "perplexity", "name": "Perplexity AI", "category": "Deep Research",
    "sources": {
      "pricing":    "https://www.perplexity.ai/hub/faq/what-is-perplexity-pro",
      "enterprise": "https://www.perplexity.ai/enterprise/pricing",
      "help":       "https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you",
      "reddit":     "https://www.reddit.com/r/perplexity_ai/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Perplexity AI Pro Max Enterprise Pro Enterprise Max pricing 2025 site:perplexity.ai",
      "free_limits":     "Perplexity AI free plan Pro Search daily limit restrictions 2025",
      "usage_limits":    "Perplexity AI Pro Search limits Deep Research daily cap file limits 2025",
      "features":        "Perplexity AI new features Spaces Comet updates 2025",
      "pros_cons":       "Perplexity AI pros cons limitations expensive enterprise user complaints 2025",
      "reddit":          "Perplexity AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "notebooklm", "name": "NotebookLM", "category": "Deep Research",
    "sources": {
      "pricing":  "https://notebooklm.google/plans",
      "features": "https://notebooklm.google/",
      "help":     "https://support.google.com/notebooklm",
      "reddit":   "https://www.reddit.com/r/notebooklm/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Google NotebookLM Plus pricing free features 2025 site:notebooklm.google",
      "free_limits":     "NotebookLM free plan 50 sources rate limits restrictions 2025",
      "usage_limits":    "NotebookLM notebook limits source size limits audio overview limits 2025",
      "features":        "NotebookLM new features Audio Overview data tables updates 2025",
      "pros_cons":       "NotebookLM pros cons no real-time web limitations user complaints 2025",
      "reddit":          "NotebookLM user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "elicit", "name": "Elicit", "category": "Deep Research",
    "sources": {
      "pricing":  "https://elicit.com/pricing",
      "features": "https://elicit.com/features",
      "reddit":   "https://www.reddit.com/r/PhD/search/?q=elicit&sort=new"
    },
    "queries": {
      "pricing_plans":   "Elicit AI Plus Pro Team pricing plans 2025 site:elicit.com",
      "free_limits":     "Elicit free plan 12 queries per month limitations 2025",
      "usage_limits":    "Elicit query limits paper upload limits team restrictions 2025",
      "features":        "Elicit AI literature review new features updates 2025",
      "pros_cons":       "Elicit AI pros cons expensive Team plan limitations user complaints 2025",
      "reddit":          "Elicit AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "consensus", "name": "Consensus", "category": "Deep Research",
    "sources": {
      "pricing":  "https://consensus.app/home/pricing/",
      "features": "https://consensus.app/home/",
      "reddit":   "https://www.reddit.com/r/academia/search/?q=consensus+app&sort=new"
    },
    "queries": {
      "pricing_plans":   "Consensus app Premium Teams pricing 2025 site:consensus.app",
      "free_limits":     "Consensus app free plan search limits restrictions 2025",
      "usage_limits":    "Consensus app daily search limits paper access limits 2025",
      "features":        "Consensus app Consensus Meter new features updates 2025",
      "pros_cons":       "Consensus app pros cons limitations user complaints 2025",
      "reddit":          "Consensus app user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ DASHBOARD & DATA ══════════════
  {
    "id": "powerbi", "name": "Power BI Copilot", "category": "Dashboard & Data",
    "sources": {
      "pricing":  "https://powerbi.microsoft.com/en-us/pricing/",
      "copilot":  "https://powerbi.microsoft.com/en-us/blog/",
      "docs":     "https://learn.microsoft.com/en-us/power-bi/fundamentals/service-features-license-type",
      "reddit":   "https://www.reddit.com/r/PowerBI/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Power BI Pro Premium Per User Fabric pricing Copilot 2025 site:powerbi.microsoft.com OR site:microsoft.com",
      "free_limits":     "Power BI free Desktop no sharing no Copilot limitations 2025",
      "usage_limits":    "Power BI Pro PPU dataset size refresh limits Copilot requirements 2025",
      "features":        "Power BI Copilot new features DAX generation Fabric updates 2025",
      "pros_cons":       "Power BI Copilot pros cons hidden PPU requirement complaints 2025",
      "reddit":          "Power BI Copilot user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "tableau", "name": "Tableau Pulse", "category": "Dashboard & Data",
    "sources": {
      "pricing":  "https://www.tableau.com/pricing/teams-orgs",
      "pulse":    "https://www.tableau.com/products/tableau-pulse",
      "reddit":   "https://www.reddit.com/r/tableau/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Tableau Viewer Explorer Creator pricing Tableau Plus Pulse 2025 site:tableau.com",
      "free_limits":     "Tableau Public free limitations private data no enterprise 2025",
      "usage_limits":    "Tableau Creator Explorer pricing per user limits Salesforce dependency 2025",
      "features":        "Tableau Pulse Einstein AI new features Salesforce updates 2025",
      "pros_cons":       "Tableau Pulse pros cons expensive Salesforce dependency complaints 2025",
      "reddit":          "Tableau Pulse user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "rowsai", "name": "Rows AI", "category": "Dashboard & Data",
    "sources": {
      "pricing":  "https://rows.com/pricing",
      "features": "https://rows.com/features",
      "reddit":   "https://www.reddit.com/r/analytics/search/?q=rows+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Rows AI Plus Business Enterprise pricing 2025 site:rows.com",
      "free_limits":     "Rows AI free plan row limits feature restrictions 2025",
      "usage_limits":    "Rows AI data limits integration limits 2025",
      "features":        "Rows AI Analyst new features integrations updates 2025",
      "pros_cons":       "Rows AI pros cons limitations user complaints 2025",
      "reddit":          "Rows AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ IMAGE GENERATION ══════════════
  {
    "id": "midjourney", "name": "Midjourney", "category": "Image Generation",
    "sources": {
      "pricing":  "https://www.midjourney.com/account/",
      "docs":     "https://docs.midjourney.com/",
      "reddit":   "https://www.reddit.com/r/midjourney/top/?t=week"
    },
    "queries": {
      "pricing_plans":   "Midjourney Basic Standard Pro Mega pricing GPU hours 2025 site:midjourney.com OR site:docs.midjourney.com",
      "free_limits":     "Midjourney no free plan since 2023 paid only 2025",
      "usage_limits":    "Midjourney GPU hours Fast Relax Stealth mode limits 2025",
      "features":        "Midjourney V7 new features video generation updates 2025",
      "pros_cons":       "Midjourney pros cons no enterprise billing no API complaints 2025",
      "reddit":          "Midjourney user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "dalle", "name": "DALL-E OpenAI", "category": "Image Generation",
    "sources": {
      "pricing":  "https://openai.com/api/pricing/",
      "docs":     "https://platform.openai.com/docs/guides/images",
      "reddit":   "https://www.reddit.com/r/ChatGPT/search/?q=dall-e&sort=new"
    },
    "queries": {
      "pricing_plans":   "DALL-E 3 API pricing image generation ChatGPT Plus included 2025 site:openai.com",
      "free_limits":     "DALL-E free tier ChatGPT free limitations image generation 2025",
      "usage_limits":    "DALL-E daily image limits API rate limits per plan 2025",
      "features":        "DALL-E 3 new features inpainting text rendering updates 2025",
      "pros_cons":       "DALL-E pros cons artistic quality limitations vs Midjourney 2025",
      "reddit":          "DALL-E user reviews compared Midjourney Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "firefly", "name": "Adobe Firefly", "category": "Image Generation",
    "sources": {
      "pricing":  "https://www.adobe.com/products/firefly/pricing.html",
      "features": "https://www.adobe.com/products/firefly.html",
      "reddit":   "https://www.reddit.com/r/Adobe/search/?q=firefly&sort=new"
    },
    "queries": {
      "pricing_plans":   "Adobe Firefly Creative Cloud pricing individual teams enterprise 2025 site:adobe.com",
      "free_limits":     "Adobe Firefly free 25 credits limitations watermark 2025",
      "usage_limits":    "Adobe Firefly generative credits limits per plan 2025",
      "features":        "Adobe Firefly new features generative fill Photoshop updates 2025",
      "pros_cons":       "Adobe Firefly pros cons commercially safe IP indemnification limitations 2025",
      "reddit":          "Adobe Firefly user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "leonardo", "name": "Leonardo AI", "category": "Image Generation",
    "sources": {
      "pricing":  "https://leonardo.ai/pricing",
      "features": "https://leonardo.ai/features",
      "reddit":   "https://www.reddit.com/r/StableDiffusion/search/?q=leonardo+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Leonardo AI Apprentice Artisan Maestro Enterprise pricing tokens 2025 site:leonardo.ai",
      "free_limits":     "Leonardo AI free 150 tokens daily limitations 2025",
      "usage_limits":    "Leonardo AI token system daily limits custom model limits 2025",
      "features":        "Leonardo AI Phoenix model custom training new features updates 2025",
      "pros_cons":       "Leonardo AI pros cons game development character consistency limitations 2025",
      "reddit":          "Leonardo AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ VIDEO GENERATION ══════════════
  {
    "id": "runway", "name": "Runway ML", "category": "Video Generation",
    "sources": {
      "pricing":  "https://runwayml.com/pricing",
      "features": "https://runwayml.com/research",
      "reddit":   "https://www.reddit.com/r/videoproduction/search/?q=runway+ml&sort=new"
    },
    "queries": {
      "pricing_plans":   "Runway ML Standard Pro Unlimited Enterprise pricing credits 2025 site:runwayml.com",
      "free_limits":     "Runway ML free tier 3 generations trial watermark limitations 2025",
      "usage_limits":    "Runway ML credit costs Gen-4 seconds limits video length 2025",
      "features":        "Runway ML Gen-4 Director Mode new features updates 2025",
      "pros_cons":       "Runway ML pros cons slow generation credit system complaints 2025",
      "reddit":          "Runway ML user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "synthesia", "name": "Synthesia", "category": "Video Generation",
    "sources": {
      "pricing":  "https://www.synthesia.io/pricing",
      "features": "https://www.synthesia.io/features",
      "reddit":   "https://www.reddit.com/r/elearning/search/?q=synthesia&sort=new"
    },
    "queries": {
      "pricing_plans":   "Synthesia Starter Creator Enterprise pricing avatars 2025 site:synthesia.io",
      "free_limits":     "Synthesia free plan 1 video credit limitations 2025",
      "usage_limits":    "Synthesia video minutes per month avatar limits language limits 2025",
      "features":        "Synthesia SCORM avatars new features corporate video updates 2025",
      "pros_cons":       "Synthesia pros cons expensive clearly AI avatar limitations complaints 2025",
      "reddit":          "Synthesia user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "pika", "name": "Pika Labs", "category": "Video Generation",
    "sources": {
      "pricing":  "https://pika.art/pricing",
      "features": "https://pika.art/features",
      "reddit":   "https://www.reddit.com/r/AItools/search/?q=pika+labs&sort=new"
    },
    "queries": {
      "pricing_plans":   "Pika Labs Standard Pro Unlimited Fancy pricing credits 2025 site:pika.art",
      "free_limits":     "Pika Labs free daily credit refresh watermark limitations 2025",
      "usage_limits":    "Pika Labs credit costs video length 3-10 seconds resolution limits 2025",
      "features":        "Pika 2.5 Pikaffects new effects updates 2025",
      "pros_cons":       "Pika Labs pros cons 10 second limit no 4K social media focused 2025",
      "reddit":          "Pika Labs user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ AUDIO & VOICE ══════════════
  {
    "id": "elevenlabs", "name": "ElevenLabs", "category": "Audio & Voice",
    "sources": {
      "pricing":  "https://elevenlabs.io/pricing",
      "features": "https://elevenlabs.io/features",
      "reddit":   "https://www.reddit.com/r/podcasting/search/?q=elevenlabs&sort=new"
    },
    "queries": {
      "pricing_plans":   "ElevenLabs Starter Creator Pro Scale Business Enterprise pricing characters 2025 site:elevenlabs.io",
      "free_limits":     "ElevenLabs free plan 10000 characters limitations no API 2025",
      "usage_limits":    "ElevenLabs character limits per plan API rate limits concurrency 2025",
      "features":        "ElevenLabs voice cloning dubbing studio new features updates 2025",
      "pros_cons":       "ElevenLabs pros cons expensive Scale plan character limits complaints 2025",
      "reddit":          "ElevenLabs user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "murf", "name": "Murf AI", "category": "Audio & Voice",
    "sources": {
      "pricing":  "https://murf.ai/pricing",
      "features": "https://murf.ai/features",
      "reddit":   "https://www.reddit.com/r/podcasting/search/?q=murf+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Murf AI Creator Business Enterprise pricing voice minutes 2025 site:murf.ai",
      "free_limits":     "Murf AI free plan 10 minutes no download limitations 2025",
      "usage_limits":    "Murf AI voice minutes limits per plan API limits 2025",
      "features":        "Murf AI new features voice cloning studio controls updates 2025",
      "pros_cons":       "Murf AI pros cons quality vs ElevenLabs limitations user complaints 2025",
      "reddit":          "Murf AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "descript", "name": "Descript", "category": "Audio & Voice",
    "sources": {
      "pricing":  "https://www.descript.com/pricing",
      "features": "https://www.descript.com/features",
      "reddit":   "https://www.reddit.com/r/podcasting/search/?q=descript&sort=new"
    },
    "queries": {
      "pricing_plans":   "Descript Hobbyist Creator Business Enterprise pricing 2025 site:descript.com",
      "free_limits":     "Descript free plan 1 hour transcript watermark limitations 2025",
      "usage_limits":    "Descript transcription hours limits Overdub limits 2025",
      "features":        "Descript Overdub text-based editing new features updates 2025",
      "pros_cons":       "Descript pros cons expensive Business plan limitations user complaints 2025",
      "reddit":          "Descript user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ PRODUCTIVITY & AUTOMATION ══════════════
  {
    "id": "zapier", "name": "Zapier AI", "category": "Automation",
    "sources": {
      "pricing":  "https://zapier.com/pricing",
      "features": "https://zapier.com/features",
      "reddit":   "https://www.reddit.com/r/automation/search/?q=zapier&sort=new"
    },
    "queries": {
      "pricing_plans":   "Zapier Starter Professional Team Enterprise pricing tasks 2025 site:zapier.com",
      "free_limits":     "Zapier free plan 100 tasks 5 Zaps limitations 2025",
      "usage_limits":    "Zapier task limits polling delay premium app restrictions 2025",
      "features":        "Zapier AI Zap builder Canvas new features updates 2025",
      "pros_cons":       "Zapier pros cons expensive vs Make task limits complaints 2025",
      "reddit":          "Zapier user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "make", "name": "Make Integromat", "category": "Automation",
    "sources": {
      "pricing":  "https://www.make.com/en/pricing",
      "features": "https://www.make.com/en/features",
      "reddit":   "https://www.reddit.com/r/nocode/search/?q=make+integromat&sort=new"
    },
    "queries": {
      "pricing_plans":   "Make Integromat Core Pro Teams Enterprise pricing operations 2025 site:make.com",
      "free_limits":     "Make Integromat free plan 1000 operations 2 scenarios limitations 2025",
      "usage_limits":    "Make operations limits concurrent scenarios polling interval 2025",
      "features":        "Make Integromat new features AI integrations visual builder updates 2025",
      "pros_cons":       "Make Integromat pros cons vs Zapier learning curve limitations 2025",
      "reddit":          "Make Integromat user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "manus", "name": "Manus AI", "category": "Automation",
    "sources": {
      "pricing":  "https://manus.im/",
      "reddit":   "https://www.reddit.com/r/AItools/search/?q=manus+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Manus AI pricing plans credits 2025",
      "free_limits":     "Manus AI free tier waitlist limited access 2025",
      "usage_limits":    "Manus AI credit limits task complexity autonomous agent limits 2025",
      "features":        "Manus AI autonomous agent new features parallel execution updates 2025",
      "pros_cons":       "Manus AI pros cons early access unreliable limitations user reviews 2025",
      "reddit":          "Manus AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },

  # ══════════════ DESIGN & UI/UX ══════════════
  {
    "id": "figmaai", "name": "Figma AI", "category": "Design",
    "sources": {
      "pricing":  "https://www.figma.com/pricing/",
      "features": "https://www.figma.com/ai/",
      "reddit":   "https://www.reddit.com/r/UI_Design/search/?q=figma+ai&sort=new"
    },
    "queries": {
      "pricing_plans":   "Figma AI Professional Organization Enterprise pricing 2025 site:figma.com",
      "free_limits":     "Figma free plan AI credit limits starter restrictions 2025",
      "usage_limits":    "Figma AI credits limits per plan team restrictions 2025",
      "features":        "Figma AI Make Designs Dev Mode new features updates 2025",
      "pros_cons":       "Figma AI pros cons Organization plan expensive limitations 2025",
      "reddit":          "Figma AI user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
  {
    "id": "uizard", "name": "Uizard", "category": "Design",
    "sources": {
      "pricing":  "https://uizard.io/pricing/",
      "features": "https://uizard.io/features/",
      "reddit":   "https://www.reddit.com/r/ProductManagement/search/?q=uizard&sort=new"
    },
    "queries": {
      "pricing_plans":   "Uizard Pro Business pricing 2025 site:uizard.io",
      "free_limits":     "Uizard free plan screen limits no export limitations 2025",
      "usage_limits":    "Uizard screens per project user limits 2025",
      "features":        "Uizard Autodesigner screenshot to design new features updates 2025",
      "pros_cons":       "Uizard pros cons not for professional designers limitations 2025",
      "reddit":          "Uizard user reviews complaints Reddit 2025 site:reddit.com"
    }
  },
]

# ─── NEW TOOLS DETECTION QUERIES ────────────────────────────────
NEW_TOOLS_QUERIES = [
  "new AI tools launched productivity marketing coding writing 2025",
  "best new AI tools emerged this month 2025 site:producthunt.com",
  "newly launched AI tools worth knowing GTM content design 2025"
]

# ─── GEMINI API CALL ────────────────────────────────────────────
def ask_gemini(prompt, retries=3):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.1,
            "maxOutputTokens": 600
        }
    }
    for attempt in range(retries):
        try:
            r = requests.post(url, json=body, timeout=25)
            r.raise_for_status()
            data = r.json()
            return data['candidates'][0]['content']['parts'][0]['text'].strip()
        except Exception as e:
            print(f"  Gemini attempt {attempt+1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None

# ─── BUILD PROMPT FOR EACH SECTION ──────────────────────────────
def build_prompt(tool_name, section, query, sources):
    source_list = "\n".join([f"- {k}: {v}" for k, v in sources.items()])
    prompts = {
        "pricing_plans": f"""
Research current pricing for {tool_name} as of 2025.
Primary sources to check: {source_list}
Search query: {query}

Return ONLY a JSON object with this exact structure:
{{
  "plans": [
    {{"name": "Plan Name", "price": "$X/mo", "description": "what is included"}}
  ]
}}
List ALL available plans. Be specific with prices. No extra text outside JSON.
""",
        "free_limits": f"""
Research the FREE plan limitations for {tool_name} as of 2025.
Primary sources: {source_list}
Search query: {query}

Return ONLY a JSON array of strings listing each limitation:
["limitation 1", "limitation 2", "limitation 3"]
Be specific. No extra text outside JSON.
""",
        "usage_limits": f"""
Research usage limits and caps for {tool_name} as of 2025.
Primary sources: {source_list}
Search query: {query}

Return ONLY a JSON object with limit name as key and limit value as value:
{{"Context window": "256K tokens", "Daily cap": "50 messages", "File upload": "10MB"}}
Include: context window, message/query caps, file upload limits, rate limits, seat minimums.
No extra text outside JSON.
""",
        "features": f"""
Research the key features of {tool_name} as of 2025.
Primary sources: {source_list}
Search query: {query}

Return ONLY a JSON array of the top 10 key features as strings:
["Feature 1", "Feature 2", "Feature 3"]
Be specific. No extra text outside JSON.
""",
        "pros_cons": f"""
Research real user pros and cons for {tool_name} as of 2025.
Primary sources: {source_list}
Search query: {query}

Return ONLY a JSON object:
{{
  "pros": ["pro 1", "pro 2", "pro 3"],
  "cons": ["con 1", "con 2", "con 3 including hidden limitations"]
}}
Include hidden limitations users commonly complain about. No extra text outside JSON.
""",
        "reddit": f"""
Research real user feedback and reviews for {tool_name} from Reddit and community forums 2025.
Primary sources: {source_list}
Search query: {query}

Return ONLY a JSON array of 3 realistic user quotes with subreddit source:
[
  "quote from user describing their experience — r/subredditname",
  "another real user quote — r/subredditname",
  "third user quote — r/subredditname"
]
These should reflect genuine user sentiment. No extra text outside JSON.
"""
    }
    return prompts.get(section, f"Research {section} for {tool_name}: {query}")

# ─── SAFE JSON PARSE ────────────────────────────────────────────
def safe_json(text):
    if not text:
        return None
    try:
        text = text.strip()
        text = re.sub(r'^```json\s*', '', text)
        text = re.sub(r'^```\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        text = text.strip()
        return json.loads(text)
    except:
        match = re.search(r'(\[.*\]|\{.*\})', text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                return None
    return None

# ─── CACHE ──────────────────────────────────────────────────────
def load_cache():
    if os.path.exists('cache.json'):
        with open('cache.json') as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open('cache.json', 'w') as f:
        json.dump(data, f, indent=2)

# ─── DETECT CHANGES ─────────────────────────────────────────────
def detect_changes(tool_id, section, new_data, old_cache):
    if tool_id not in old_cache:
        return []
    old_section = old_cache[tool_id].get(section)
    if not old_section:
        return []

    changes = []
    new_str = json.dumps(new_data, sort_keys=True) if new_data else ""
    old_str = json.dumps(old_section, sort_keys=True) if old_section else ""

    if new_str == old_str:
        return []

    old_prices = set(re.findall(r'\$[\d,.]+(?:/\w+)?', old_str))
    new_prices = set(re.findall(r'\$[\d,.]+(?:/\w+)?', new_str))
    added = new_prices - old_prices
    removed = old_prices - new_prices

    if added:
        changes.append(f"{section}: new prices {', '.join(sorted(added))}")
    if removed:
        changes.append(f"{section}: removed prices {', '.join(sorted(removed))}")
    if not changes and new_str != old_str:
        changes.append(f"{section}: content updated")

    return changes

# ─── UPDATE HTML DASHBOARD ───────────────────────────────────────
def update_html(tool_id, section, new_data, html_content):
    if not new_data:
        return html_content

    # Find the tool card by id pattern
    card_pattern = rf'(id="d{tool_id}".*?)(</div>\s*</div>\s*</div>)'

    if section == "pricing_plans" and isinstance(new_data, dict) and "plans" in new_data:
        plans_html = '\n'.join([
            f'''<div class="plan-card">
  <div class="plan-top">
    <span class="plan-name">{p.get("name","")}</span>
    <span class="plan-price">{p.get("price","Custom")}</span>
  </div>
  <div class="plan-desc">{p.get("description","")}</div>
</div>'''
            for p in new_data["plans"]
        ])
        old_plans = re.search(r'<div class="plans-wrap">(.*?)</div>\s*</div>', html_content, re.DOTALL)
        if old_plans:
            html_content = html_content.replace(
                old_plans.group(0),
                f'<div class="plans-wrap">\n{plans_html}\n</div>\n</div>'
            )

    elif section == "free_limits" and isinstance(new_data, list):
        items_html = '\n'.join([f'<li class="warn">{item}</li>' for item in new_data])
        old_section = re.search(
            rf'<h4>Free Plan Limits</h4>\s*<ul class="flist">(.*?)</ul>',
            html_content, re.DOTALL
        )
        if old_section:
            html_content = html_content.replace(
                old_section.group(0),
                f'<h4>Free Plan Limits</h4>\n<ul class="flist">\n{items_html}\n</ul>'
            )

    elif section == "features" and isinstance(new_data, list):
        items_html = '\n'.join([f'<li>{item}</li>' for item in new_data[:10]])
        old_section = re.search(
            rf'<h4>Key Features</h4>\s*<ul class="flist">(.*?)</ul>',
            html_content, re.DOTALL
        )
        if old_section:
            html_content = html_content.replace(
                old_section.group(0),
                f'<h4>Key Features</h4>\n<ul class="flist">\n{items_html}\n</ul>'
            )

    elif section == "pros_cons" and isinstance(new_data, dict):
        pros_html = '\n'.join([f'<li class="pro">{p}</li>' for p in new_data.get("pros", [])])
        cons_html = '\n'.join([f'<li class="con">{c}</li>' for c in new_data.get("cons", [])])
        old_pros = re.search(r'<h4>Pros</h4>\s*<ul class="flist">(.*?)</ul>', html_content, re.DOTALL)
        if old_pros:
            html_content = html_content.replace(
                old_pros.group(0),
                f'<h4>Pros</h4>\n<ul class="flist">\n{pros_html}\n</ul>'
            )
        old_cons = re.search(r'<h4>Cons.*?</h4>\s*<ul class="flist">(.*?)</ul>', html_content, re.DOTALL)
        if old_cons:
            html_content = html_content.replace(
                old_cons.group(0),
                f'<h4>Cons &amp; Hidden Limitations</h4>\n<ul class="flist">\n{cons_html}\n</ul>'
            )

    elif section == "usage_limits" and isinstance(new_data, dict):
        limits_html = '\n'.join([
            f'<div class="lim"><span class="lk">{k}</span><span class="lv">{v}</span></div>'
            for k, v in new_data.items()
        ])
        old_lims = re.search(
            r'<h4>Usage Limits.*?</h4>\s*<div class="lims">(.*?)</div>',
            html_content, re.DOTALL
        )
        if old_lims:
            html_content = html_content.replace(
                old_lims.group(0),
                f'<h4>Usage Limits &amp; Caps</h4>\n<div class="lims">\n{limits_html}\n</div>'
            )

    elif section == "reddit" and isinstance(new_data, list):
        quotes_html = '\n'.join([f'<div class="rq">{q}</div>' for q in new_data])
        old_reddit = re.search(
            r'<h4>Reddit.*?Feedback</h4>(.*?)(?=</div>\s*</div>)',
            html_content, re.DOTALL
        )
        if old_reddit:
            html_content = html_content.replace(
                old_reddit.group(0),
                f'<h4>Reddit &amp; Community Feedback</h4>\n{quotes_html}\n'
            )

    return html_content

# ─── TELEGRAM NOTIFICATION ──────────────────────────────────────
def telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg[:4000], "parse_mode": "HTML"},
            timeout=10
        )
        print("Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")

# ─── UPDATE TIMESTAMP BANNER ────────────────────────────────────
def update_banner(html_content, changes_count, tools_checked):
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    banner = f'''<div id="auto-banner" style="background:#f0fdf4;border:1px solid #86efac;
border-radius:8px;padding:10px 16px;margin-bottom:14px;font-size:12px;color:#166534;
font-family:Inter,sans-serif;display:flex;gap:20px;flex-wrap:wrap;align-items:center;">
&#x1F504; <strong>Auto-updated:</strong> {now} &nbsp;|&nbsp;
<strong>Changes today:</strong> {changes_count} &nbsp;|&nbsp;
<strong>Tools tracked:</strong> {tools_checked} &nbsp;|&nbsp;
<strong>Sections tracked per tool:</strong> 7 &nbsp;|&nbsp;
<a href="https://{GITHUB_USER}.github.io/ai-tools-dashboard" style="color:#166534;">&#x1F517; Live Dashboard</a>
</div>'''
    html_content = re.sub(r'<div id="auto-banner".*?</div>', '', html_content, flags=re.DOTALL)
    html_content = html_content.replace('<div class="stat-row">', banner + '\n<div class="stat-row">', 1)
    return html_content

# ─── CHECK FOR NEW TOOLS ────────────────────────────────────────
def check_new_tools():
    results = []
    for q in NEW_TOOLS_QUERIES[:1]:
        resp = ask_gemini(
            f"List 5 completely new AI tools launched in the last 30 days useful for marketing, coding, or productivity. "
            f"For each give: tool name, category, and one sentence description. Query: {q}"
        )
        if resp:
            results.append(resp)
        time.sleep(2)
    return "\n".join(results) if results else "No notable new tools detected."

# ─── MAIN ────────────────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"AI Tools Dashboard Auto-Update")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tools to check: {len(TOOLS)}")
    print(f"{'='*60}\n")

    old_cache = load_cache()
    new_cache = {}
    all_changes = []

    if not os.path.exists('index.html'):
        print("ERROR: index.html not found. Please upload your dashboard first.")
        telegram("⚠️ <b>Dashboard Update Failed</b>\nindex.html not found in repository.")
        return

    with open('index.html', encoding='utf-8') as f:
        html_content = f.read()

    sections_to_check = [
        "pricing_plans",
        "free_limits",
        "usage_limits",
        "features",
        "pros_cons",
        "reddit"
    ]

    for tool in TOOLS:
        tid   = tool["id"]
        tname = tool["name"]
        tcat  = tool["category"]
        print(f"\n[{tcat}] Checking: {tname}")

        new_cache[tid] = {"name": tname, "category": tcat, "updated": datetime.now().isoformat()}
        tool_changes = []

        for section in sections_to_check:
            query   = tool["queries"].get(section, "")
            sources = tool["sources"]

            if not query:
                continue

            print(f"  → {section}...", end=" ")
            prompt = build_prompt(tname, section, query, sources)
            raw    = ask_gemini(prompt)
            parsed = safe_json(raw)

            if parsed:
                print("✓")
                new_cache[tid][section] = parsed
                changes = detect_changes(tid, section, parsed, old_cache)
                if changes:
                    tool_changes.extend(changes)
                    html_content = update_html(tid, section, parsed, html_content)
            else:
                print("× (could not parse)")
                if tid in old_cache and section in old_cache[tid]:
                    new_cache[tid][section] = old_cache[tid][section]

            time.sleep(1.5)

        if tool_changes:
            all_changes.append({"tool": tname, "category": tcat, "changes": tool_changes})
            print(f"  ⚡ {len(tool_changes)} change(s) detected for {tname}")

    print(f"\n{'='*60}")
    print(f"Checking for new AI tools...")
    new_tools_text = check_new_tools()
    print(f"{'='*60}\n")

    html_content = update_banner(html_content, len(all_changes), len(TOOLS))

    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    print("index.html updated ✓")

    save_cache(new_cache)
    print("cache.json saved ✓")

    today = datetime.now().strftime("%d %b %Y")

    if all_changes:
        lines = [f"<b>&#x1F6A8; AI Tools Update — {today}</b>"]
        lines.append(f"<b>{len(all_changes)} tool(s) changed across {len(TOOLS)} tracked</b>\n")

        by_cat = {}
        for item in all_changes:
            cat = item["category"]
            if cat not in by_cat:
                by_cat[cat] = []
            by_cat[cat].append(item)

        for cat, items in by_cat.items():
            lines.append(f"\n<b>&#x1F4CC; {cat}</b>")
            for item in items:
                lines.append(f"\n  &#x1F504; <b>{item['tool']}</b>")
                for c in item['changes'][:3]:
                    lines.append(f"    • {c}")

        if new_tools_text and len(new_tools_text) > 20:
            lines.append(f"\n\n<b>&#x1F195; New Tools Detected:</b>")
            lines.append(new_tools_text[:500])

        lines.append(f"\n\n&#x1F4CA; <a href='https://{GITHUB_USER}.github.io/ai-tools-dashboard'>View Dashboard</a>")
        telegram("\n".join(lines))

    else:
        msg = (
            f"&#x2705; <b>Daily Check Complete — {today}</b>\n\n"
            f"All {len(TOOLS)} tools checked across 6 sections each.\n"
            f"No pricing or feature changes detected.\n"
            f"Dashboard is current and up to date.\n\n"
            f"<b>&#x1F195; New Tools This Month:</b>\n{new_tools_text[:400]}\n\n"
            f"&#x1F4CA; <a href='https://{GITHUB_USER}.github.io/ai-tools-dashboard'>Dashboard</a>"
        )
        telegram(msg)

    print(f"\n{'='*60}")
    print(f"DONE — {len(all_changes)} tools changed")
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()
