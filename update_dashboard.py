"""
AI Tools Dashboard Auto-Updater — Final Version
================================================
Architecture:
  1. Scrapes top official sources per tool (pricing page + features page)
  2. NVIDIA NIM API structures scraped content into clean JSON
  3. Reddit API fetches real community feedback
  4. Writes data.json (loaded by index.html on every page visit)
  5. Updates index.html banner with IST timestamp
  6. Telegram notification with changes summary (IST)
  7. Sources per tool tracked — shown at end of each widget
  8. Only updates a section if the new data actually differs from cached
"""

import os, json, re, time, requests
from datetime import datetime, timezone, timedelta

# ── TIMEZONE (IST = UTC+5:30) ────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

def fmt_ist(dt=None):
    if dt is None:
        dt = now_ist()
    return dt.strftime("%d %b %Y, %I:%M %p IST")

# ── CREDENTIALS ─────────────────────────────────────────────────
NVIDIA_KEY  = os.environ['GEMINI_API_KEY']
TG_TOKEN    = os.environ['TELEGRAM_BOT_TOKEN']
TG_CHAT     = os.environ['TELEGRAM_CHAT_ID']
GITHUB_USER = os.environ.get('GITHUB_USERNAME', 'yourusername')

# ── NVIDIA NIM API ───────────────────────────────────────────────
NVIDIA_URL   = "https://integrate.api.nvidia.com/v1/chat/completions"
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
# Fallback if above gives 404:
# NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
# NVIDIA_MODEL = "mistralai/mixtral-8x22b-instruct-v0.1"

# ── HTTP HEADERS FOR SCRAPING ────────────────────────────────────
WEB_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7",
}

# ── ALL 50 TOOLS (matching index.html IDs and official URLs) ─────
TOOLS = [
  # GENERAL AI ASSISTANT
  {"id":"chatgpt","name":"ChatGPT","cat":"General AI",
   "scrape_urls":["https://openai.com/chatgpt/pricing","https://openai.com/enterprise"],
   "reddit_sub":"ChatGPT","reddit_q":"ChatGPT pricing plans update 2025"},

  {"id":"claude","name":"Claude","cat":"General AI",
   "scrape_urls":["https://claude.ai/pricing","https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan"],
   "reddit_sub":"ClaudeAI","reddit_q":"Claude AI pricing plans usage limits 2025"},

  {"id":"gemini","name":"Google Gemini","cat":"General AI",
   "scrape_urls":["https://one.google.com/intl/en/about/google-ai-plans/","https://workspace.google.com/intl/en/pricing"],
   "reddit_sub":"Gemini","reddit_q":"Google Gemini AI pricing plans review 2025"},

  {"id":"m365","name":"Microsoft 365 Copilot","cat":"General AI",
   "scrape_urls":["https://www.microsoft.com/en-us/microsoft-365-copilot/pricing-new","https://www.microsoft.com/en-us/microsoft-365-copilot/pricing/enterprise"],
   "reddit_sub":"Office365","reddit_q":"Microsoft 365 Copilot pricing plans review 2025"},

  # RESEARCH & SEARCH
  {"id":"perplexity","name":"Perplexity","cat":"Research",
   "scrape_urls":["https://www.perplexity.ai/pro","https://www.perplexity.ai/enterprise/pricing","https://www.perplexity.ai/help-center/en/articles/11187416-which-perplexity-subscription-plan-is-right-for-you"],
   "reddit_sub":"perplexity_ai","reddit_q":"Perplexity AI pro pricing limits review 2025"},

  {"id":"notebooklm","name":"NotebookLM","cat":"Research",
   "scrape_urls":["https://notebooklm.google/plans","https://notebooklm.google/"],
   "reddit_sub":"notebooklm","reddit_q":"NotebookLM review features limits 2025"},

  {"id":"elicit","name":"Elicit","cat":"Research",
   "scrape_urls":["https://elicit.com/pricing","https://elicit.com/"],
   "reddit_sub":"PhD","reddit_q":"Elicit AI research tool pricing review 2025"},

  {"id":"consensus","name":"Consensus","cat":"Research",
   "scrape_urls":["https://consensus.app/home/pricing/","https://consensus.app/"],
   "reddit_sub":"academia","reddit_q":"Consensus app AI research pricing 2025"},

  # WRITING & CONTENT
  {"id":"grammarly","name":"Grammarly","cat":"Content",
   "scrape_urls":["https://www.grammarly.com/plans","https://www.grammarly.com/business"],
   "reddit_sub":"writing","reddit_q":"Grammarly pricing plans review 2025"},

  {"id":"jasper","name":"Jasper","cat":"Content",
   "scrape_urls":["https://www.jasper.ai/pricing","https://www.jasper.ai/features"],
   "reddit_sub":"marketing","reddit_q":"Jasper AI pricing review pros cons 2025"},

  {"id":"writesonic","name":"Writesonic","cat":"Content",
   "scrape_urls":["https://writesonic.com/pricing","https://writesonic.com/features"],
   "reddit_sub":"SEO","reddit_q":"Writesonic pricing SEO content review 2025"},

  {"id":"copyai","name":"Copy.ai","cat":"Content",
   "scrape_urls":["https://www.copy.ai/pricing","https://www.copy.ai/features"],
   "reddit_sub":"Entrepreneur","reddit_q":"Copy.ai pricing GTM review 2025"},

  {"id":"notionai","name":"Notion AI","cat":"Content",
   "scrape_urls":["https://www.notion.com/pricing","https://www.notion.com/product/ai"],
   "reddit_sub":"Notion","reddit_q":"Notion AI pricing review features 2025"},

  # CODING & DEVELOPMENT
  {"id":"ghcopilot","name":"GitHub Copilot","cat":"Coding",
   "scrape_urls":["https://github.com/features/copilot/plans","https://docs.github.com/en/copilot"],
   "reddit_sub":"programming","reddit_q":"GitHub Copilot pricing review enterprise 2025"},

  {"id":"cursor","name":"Cursor","cat":"Coding",
   "scrape_urls":["https://www.cursor.com/pricing","https://docs.cursor.com/"],
   "reddit_sub":"cursor","reddit_q":"Cursor AI IDE pricing review pros cons 2025"},

  {"id":"codex","name":"OpenAI Codex","cat":"Coding",
   "scrape_urls":["https://openai.com/api/pricing/","https://openai.com/codex"],
   "reddit_sub":"OpenAI","reddit_q":"OpenAI Codex pricing features agent 2025"},

  {"id":"tabnine","name":"Tabnine","cat":"Coding",
   "scrape_urls":["https://www.tabnine.com/pricing","https://www.tabnine.com/enterprise"],
   "reddit_sub":"programming","reddit_q":"Tabnine pricing enterprise on-premises review 2025"},

  {"id":"replit","name":"Replit Ghostwriter","cat":"Coding",
   "scrape_urls":["https://replit.com/pricing","https://replit.com/ai"],
   "reddit_sub":"replit","reddit_q":"Replit Ghostwriter pricing review limitations 2025"},

  {"id":"codeium","name":"Codeium","cat":"Coding",
   "scrape_urls":["https://codeium.com/pricing","https://windsurf.com/pricing"],
   "reddit_sub":"programming","reddit_q":"Codeium Windsurf pricing free tier review 2025"},

  {"id":"claudecode","name":"Claude Code","cat":"Coding",
   "scrape_urls":["https://claude.com/product/claude-code","https://claude.ai/pricing","https://docs.anthropic.com/en/docs/claude-code/overview"],
   "reddit_sub":"ClaudeAI","reddit_q":"Claude Code agentic coding pricing review 2025"},

  {"id":"autogen","name":"AutoGen","cat":"Coding",
   "scrape_urls":["https://github.com/microsoft/autogen","https://microsoft.github.io/autogen/"],
   "reddit_sub":"LocalLLaMA","reddit_q":"AutoGen Microsoft multi-agent framework review 2025"},

  # WEB APP / NO-CODE
  {"id":"v0","name":"v0","cat":"WebApp",
   "scrape_urls":["https://v0.dev/pricing","https://v0.dev/docs"],
   "reddit_sub":"webdev","reddit_q":"v0 Vercel pricing credits review frontend 2025"},

  {"id":"bubble","name":"Bubble","cat":"WebApp",
   "scrape_urls":["https://bubble.io/pricing","https://bubble.io/features"],
   "reddit_sub":"nocode","reddit_q":"Bubble no-code pricing review production apps 2025"},

  {"id":"softr","name":"Softr","cat":"WebApp",
   "scrape_urls":["https://www.softr.io/pricing","https://www.softr.io/features"],
   "reddit_sub":"nocode","reddit_q":"Softr Airtable no-code pricing review 2025"},

  {"id":"durable","name":"Durable","cat":"WebApp",
   "scrape_urls":["https://durable.co/pricing","https://durable.co/features"],
   "reddit_sub":"smallbusiness","reddit_q":"Durable AI website builder review pricing 2025"},

  {"id":"lovable","name":"Lovable AI","cat":"WebApp",
   "scrape_urls":["https://lovable.dev/pricing","https://lovable.dev/features"],
   "reddit_sub":"vibecoding","reddit_q":"Lovable AI app builder pricing credits review 2025"},

  # DESIGN & UI/UX
  {"id":"figmaai","name":"Figma AI","cat":"Design",
   "scrape_urls":["https://www.figma.com/ai/","https://www.figma.com/pricing/"],
   "reddit_sub":"UI_Design","reddit_q":"Figma AI features pricing review designers 2025"},

  {"id":"uizard","name":"Uizard","cat":"Design",
   "scrape_urls":["https://uizard.io/pricing/","https://uizard.io/features/"],
   "reddit_sub":"ProductManagement","reddit_q":"Uizard UI design AI pricing review 2025"},

  {"id":"canva","name":"Canva Magic Studio","cat":"Design",
   "scrape_urls":["https://www.canva.com/pricing/","https://www.canva.com/magic/","https://www.canva.com/enterprise/"],
   "reddit_sub":"graphic_design","reddit_q":"Canva Magic Studio pricing review AI features 2025"},

  # IMAGE GENERATION
  {"id":"midjourney","name":"Midjourney","cat":"Image",
   "scrape_urls":["https://docs.midjourney.com/docs/plans","https://www.midjourney.com/account"],
   "reddit_sub":"midjourney","reddit_q":"Midjourney pricing plans GPU hours review 2025"},

  {"id":"dalle","name":"DALL-E","cat":"Image",
   "scrape_urls":["https://openai.com/api/pricing/","https://openai.com/index/dall-e-3/"],
   "reddit_sub":"dalle","reddit_q":"DALL-E 3 pricing ChatGPT image generation review 2025"},

  {"id":"firefly","name":"Adobe Firefly","cat":"Image",
   "scrape_urls":["https://www.adobe.com/products/firefly/pricing.html","https://www.adobe.com/creativecloud/plans.html"],
   "reddit_sub":"Adobe","reddit_q":"Adobe Firefly pricing Creative Cloud review 2025"},

  {"id":"leonardo","name":"Leonardo AI","cat":"Image",
   "scrape_urls":["https://leonardo.ai/pricing","https://leonardo.ai/features"],
   "reddit_sub":"StableDiffusion","reddit_q":"Leonardo AI pricing tokens review 2025"},

  # VIDEO GENERATION
  {"id":"runway","name":"Runway","cat":"Video",
   "scrape_urls":["https://runwayml.com/pricing","https://runwayml.com/research"],
   "reddit_sub":"videoproduction","reddit_q":"Runway ML Gen-4 pricing review 2025"},

  {"id":"synthesia","name":"Synthesia","cat":"Video",
   "scrape_urls":["https://www.synthesia.io/pricing","https://www.synthesia.io/features","https://www.synthesia.io/enterprise"],
   "reddit_sub":"elearning","reddit_q":"Synthesia pricing enterprise avatar video 2025"},

  {"id":"pika","name":"Pika","cat":"Video",
   "scrape_urls":["https://pika.art/pricing","https://pika.art/"],
   "reddit_sub":"AItools","reddit_q":"Pika Labs pricing credits video effects review 2025"},

  # AUDIO & VOICE
  {"id":"elevenlabs","name":"ElevenLabs","cat":"Audio",
   "scrape_urls":["https://elevenlabs.io/pricing","https://elevenlabs.io/features"],
   "reddit_sub":"podcasting","reddit_q":"ElevenLabs pricing voice cloning review 2025"},

  {"id":"murf","name":"Murf","cat":"Audio",
   "scrape_urls":["https://murf.ai/pricing","https://murf.ai/features"],
   "reddit_sub":"podcasting","reddit_q":"Murf AI pricing voice studio review 2025"},

  {"id":"descript","name":"Descript","cat":"Audio",
   "scrape_urls":["https://www.descript.com/pricing","https://www.descript.com/features"],
   "reddit_sub":"podcasting","reddit_q":"Descript Overdub podcast editing pricing review 2025"},

  # PRODUCTIVITY & AUTOMATION
  {"id":"zapier","name":"Zapier AI","cat":"Automation",
   "scrape_urls":["https://zapier.com/pricing","https://zapier.com/ai"],
   "reddit_sub":"automation","reddit_q":"Zapier AI pricing automation review 2025"},

  {"id":"make","name":"Make","cat":"Automation",
   "scrape_urls":["https://www.make.com/en/pricing","https://www.make.com/en/features"],
   "reddit_sub":"nocode","reddit_q":"Make Integromat pricing automation review vs Zapier 2025"},

  {"id":"agenticworkers","name":"Agentic Workers","cat":"Automation",
   "scrape_urls":["https://www.agenticworkers.com/"],
   "reddit_sub":"AItools","reddit_q":"Agentic Workers AI automation review pricing 2025"},

  {"id":"manus","name":"Manus","cat":"Automation",
   "scrape_urls":["https://manus.im/"],
   "reddit_sub":"AItools","reddit_q":"Manus AI autonomous agent pricing review 2025"},

  {"id":"workbeaver","name":"Workbeaver","cat":"Automation",
   "scrape_urls":["https://workbeaver.com/"],
   "reddit_sub":"AItools","reddit_q":"Workbeaver AI automation review pricing 2025"},

  # PRESENTATION & DOCUMENTS
  {"id":"gamma","name":"Gamma","cat":"Presentation",
   "scrape_urls":["https://gamma.app/pricing","https://gamma.app/features"],
   "reddit_sub":"productivity","reddit_q":"Gamma app presentation pricing review credits 2025"},

  {"id":"beautifulai","name":"Beautiful.ai","cat":"Presentation",
   "scrape_urls":["https://www.beautiful.ai/pricing","https://www.beautiful.ai/features"],
   "reddit_sub":"productivity","reddit_q":"Beautiful.ai presentation pricing review 2025"},

  {"id":"tome","name":"Tome","cat":"Presentation",
   "scrape_urls":["https://tome.app/pricing","https://tome.app/"],
   "reddit_sub":"startups","reddit_q":"Tome AI presentation tool pricing review 2025"},

  # DATA & ANALYTICS
  {"id":"powerbi","name":"Power BI Copilot","cat":"Analytics",
   "scrape_urls":["https://powerbi.microsoft.com/en-us/pricing/","https://learn.microsoft.com/en-us/power-bi/create-reports/copilot-introduction"],
   "reddit_sub":"PowerBI","reddit_q":"Power BI Copilot pricing PPU Fabric review 2025"},

  {"id":"tableau","name":"Tableau Pulse","cat":"Analytics",
   "scrape_urls":["https://www.tableau.com/pricing/teams-orgs","https://www.tableau.com/products/tableau-pulse"],
   "reddit_sub":"tableau","reddit_q":"Tableau Pulse pricing AI review Salesforce 2025"},

  {"id":"rowsai","name":"Rows AI","cat":"Analytics",
   "scrape_urls":["https://rows.com/pricing","https://rows.com/ai"],
   "reddit_sub":"analytics","reddit_q":"Rows AI spreadsheet pricing review 2025"},
]

TOTAL = len(TOOLS)  # Should be 50


# ── SCRAPE WEB PAGE ──────────────────────────────────────────────
def scrape_url(url: str, max_chars: int = 5000) -> str:
    """Fetch a web page and return clean visible text."""
    try:
        r = requests.get(url, headers=WEB_HEADERS, timeout=15)
        r.raise_for_status()
        # Basic HTML stripping
        text = r.text
        # Remove scripts, styles, and nav
        for tag in ['script', 'style', 'nav', 'footer', 'head', 'noscript', 'svg']:
            text = re.sub(rf'<{tag}[\s\S]*?</{tag}>', ' ', text, flags=re.IGNORECASE)
        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        # Decode HTML entities
        text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>') \
                   .replace('&nbsp;', ' ').replace('&quot;', '"').replace('&#39;', "'")
        # Collapse whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:max_chars]
    except Exception as e:
        print(f"    ⚠ scrape failed {url}: {type(e).__name__}")
        return ""


def scrape_multiple(urls: list, combined_max: int = 7000) -> str:
    """Scrape multiple URLs and combine their text."""
    parts = []
    per_url = combined_max // max(len(urls), 1)
    for url in urls:
        text = scrape_url(url, max_chars=per_url)
        if text:
            parts.append(f"[Source: {url}]\n{text}")
        time.sleep(1.2)
    return "\n\n".join(parts)[:combined_max]


# ── REDDIT FETCH ─────────────────────────────────────────────────
def fetch_reddit(tool_name: str, subreddit: str, query: str) -> list:
    """Fetch real Reddit community feedback."""
    quotes = []

    # Try subreddit search
    for search_url in [
        f"https://www.reddit.com/r/{subreddit}/search.json?q={requests.utils.quote(query)}&sort=relevance&t=month&limit=10",
        f"https://www.reddit.com/search.json?q={requests.utils.quote(query+' '+tool_name)}&sort=relevance&t=month&limit=10",
    ]:
        try:
            r = requests.get(
                search_url,
                headers={"User-Agent": "AI-Tools-Dashboard/2.0 (academic research tool)"},
                timeout=15
            )
            if r.status_code != 200:
                continue
            data = r.json()
            posts = data.get("data", {}).get("children", [])
            for post in posts:
                pd = post.get("data", {})
                title = pd.get("title", "").strip()
                body  = pd.get("selftext", "").strip()
                sub   = pd.get("subreddit", subreddit)
                score = pd.get("score", 0)

                if score < 3:
                    continue

                # Prefer body text if substantial, else use title
                text = body if len(body) > 50 else title
                if len(text) < 25:
                    continue

                # Clean and truncate
                text = re.sub(r'\s+', ' ', text).strip()
                text = text[:220].rstrip()
                if len(text) >= 220:
                    # Find last complete sentence
                    last_period = text.rfind('. ')
                    if last_period > 100:
                        text = text[:last_period + 1]
                    else:
                        text = text + "..."

                quote = f'"{text}" — r/{sub}'
                if quote not in quotes:
                    quotes.append(quote)

                if len(quotes) >= 3:
                    break

            if len(quotes) >= 2:
                break
            time.sleep(1)
        except Exception as e:
            print(f"    ⚠ Reddit error: {type(e).__name__}")

    return quotes[:3]


# ── NVIDIA NIM API ───────────────────────────────────────────────
def ask_nvidia(system_msg: str, user_msg: str, retries: int = 3) -> str | None:
    """Call NVIDIA NIM API (OpenAI-compatible format)."""
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": system_msg},
            {"role": "user",   "content": user_msg}
        ],
        "temperature": 0.05,
        "max_tokens": 1000,
        "top_p": 0.9
    }

    for attempt in range(retries):
        try:
            r = requests.post(NVIDIA_URL, headers=headers, json=body, timeout=40)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            if code in [401, 403]:
                print(f"    ✗ Auth error (HTTP {code}) — check NVIDIA API key in GitHub Secrets")
                return None
            if code == 429:
                wait = (attempt + 1) * 20
                print(f"    ⏳ Rate limited — waiting {wait}s")
                time.sleep(wait)
            elif code == 404:
                print(f"    ✗ Model not found — check NVIDIA_MODEL setting")
                return None
            else:
                print(f"    ✗ HTTP {code} attempt {attempt+1}")
                time.sleep(5)
        except Exception as e:
            print(f"    ✗ API error attempt {attempt+1}: {type(e).__name__}: {e}")
            time.sleep(4)

    return None


# ── SAFE JSON PARSE ──────────────────────────────────────────────
SYS = (
    "You are a precise AI tool data researcher. "
    "Always respond with valid JSON ONLY. "
    "No markdown, no code fences, no extra text. "
    "Never use undefined or null — use empty string for missing values."
)

def safe_json(text: str):
    if not text:
        return None
    t = text.strip()
    # Strip markdown fences if model added them
    t = re.sub(r'^```(?:json)?\s*', '', t, flags=re.MULTILINE)
    t = re.sub(r'```\s*$', '', t, flags=re.MULTILINE)
    t = t.strip()

    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass

    # Try extracting outermost array or object
    for pat in [r'(\[[\s\S]*\])', r'(\{[\s\S]*\})']:
        m = re.search(pat, t)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                pass
    return None


# ── EXTRACT PRICING PLANS ────────────────────────────────────────
def extract_plans(tool_name: str, page_text: str) -> list:
    if not page_text.strip():
        return []

    prompt = f"""Extract EVERY pricing plan for {tool_name} from this official page content.
Include free plans, trial plans, all paid tiers, enterprise tiers. Do NOT miss any plan.
For unknown prices use "Custom — contact sales".

Page content:
{page_text[:4000]}

Respond with ONLY a JSON array. No other text:
[{{"n":"Plan Name","p":"$X/month or custom","d":"What is included in this plan, key features and limits"}}]"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed
    return []


# ── EXTRACT FREE LIMITS ──────────────────────────────────────────
def extract_free_limits(tool_name: str, page_text: str) -> list:
    if not page_text.strip():
        return []

    prompt = f"""From this official page for {tool_name}, list ALL FREE PLAN LIMITATIONS.
Include: message limits, feature restrictions, storage caps, no X features, watermarks, trial periods.
If no free plan exists, return: ["No free plan — paid subscription or trial required"]

Page content:
{page_text[:3000]}

Respond with ONLY a JSON array of strings. No other text:
["Limitation 1","Limitation 2","Limitation 3"]"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed
    return []


# ── EXTRACT USAGE LIMITS ─────────────────────────────────────────
def extract_limits(tool_name: str, page_text: str) -> dict:
    if not page_text.strip():
        return {}

    prompt = f"""From this official page for {tool_name}, extract all USAGE LIMITS AND CAPS.
Include context window, message/query daily cap, file upload limit, storage, API rate limits, seat minimums.

Page content:
{page_text[:3000]}

Respond with ONLY a JSON object. No other text:
{{"Limit name":"Limit value","Limit name 2":"Limit value 2"}}"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, dict):
        return {k: v for k, v in parsed.items() if v and str(v).strip()}
    return {}


# ── EXTRACT FEATURES ─────────────────────────────────────────────
def extract_features(tool_name: str, page_text: str) -> list:
    if not page_text.strip():
        return []

    prompt = f"""From this official page for {tool_name}, list the TOP 10 KEY FEATURES.
Be specific — real features users care about, not marketing fluff.

Page content:
{page_text[:3000]}

Respond with ONLY a JSON array of 10 feature strings. No other text:
["Feature 1","Feature 2","Feature 3"]"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed[:12]
    return []


# ── RESEARCH PROS / CONS ─────────────────────────────────────────
def research_pros_cons(tool_name: str, page_text: str) -> dict:
    prompt = f"""Research real user pros, cons, and hidden limitations for {tool_name} in 2025.
Use both the page content below AND your knowledge of real user complaints.
Focus on hidden costs, undisclosed limits, common complaints, and genuine advantages.

Page content snippet:
{page_text[:1500]}

Respond with ONLY this JSON. No other text:
{{"pros":["Advantage 1","Advantage 2","Advantage 3","Advantage 4","Advantage 5"],"cons":["Hidden cost or limit 1","User complaint 2","Undisclosed issue 3","Limitation 4","Limitation 5"]}}"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, dict) and ("pros" in parsed or "cons" in parsed):
        return parsed
    return {"pros": [], "cons": []}


# ── RESEARCH USE CASES ───────────────────────────────────────────
def research_uses(tool_name: str) -> list:
    prompt = f"""List the TOP 8 PRACTICAL USE CASES for {tool_name} in 2025.
Be specific and practical — what do real users actually use it for daily?

Respond with ONLY a JSON array. No other text:
["Use case 1","Use case 2","Use case 3"]"""

    raw = ask_nvidia(SYS, prompt)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) > 0:
        return parsed[:10]
    return []


# ── CACHE FUNCTIONS ──────────────────────────────────────────────
def load_cache() -> dict:
    try:
        if os.path.exists("cache.json"):
            with open("cache.json") as f:
                return json.load(f)
    except:
        pass
    return {}


def save_cache(data: dict):
    with open("cache.json", "w") as f:
        json.dump(data, f, indent=2)


# ── CHANGE DETECTION ─────────────────────────────────────────────
def has_changed(tid: str, section: str, new_data, old_cache: dict) -> bool:
    """Return True only if content actually changed."""
    if tid not in old_cache or section not in old_cache[tid]:
        return True  # First time tracking

    old_str = json.dumps(old_cache[tid].get(section, ""), sort_keys=True)
    new_str = json.dumps(new_data, sort_keys=True)
    return old_str != new_str


def describe_change(section: str, new_data, old_data) -> str:
    """Generate human-readable description of what changed."""
    old_str = json.dumps(old_data, sort_keys=True)
    new_str = json.dumps(new_data, sort_keys=True)

    old_prices = set(re.findall(r'\$[\d,]+(?:\.\d+)?(?:/\w+)?', old_str))
    new_prices  = set(re.findall(r'\$[\d,]+(?:\.\d+)?(?:/\w+)?', new_str))
    added   = new_prices - old_prices
    removed = old_prices - new_prices

    if added:
        return f"{section}: new prices — {', '.join(sorted(added))}"
    if removed:
        return f"{section}: prices removed — {', '.join(sorted(removed))}"
    return f"{section}: content updated"


# ── UPDATE HTML BANNER ───────────────────────────────────────────
def update_html_banner(changes_count: int, tools_count: int):
    """Update ONLY the auto-banner in index.html — nothing else."""
    if not os.path.exists("index.html"):
        print("⚠ index.html not found — skipping banner update")
        return

    with open("index.html", encoding="utf-8") as f:
        html = f.read()

    now = fmt_ist()
    # Update banner span content via innerHTML approach in the static HTML
    # We do this by finding the spans and replacing their content
    html = re.sub(r'(<span id="bn-time">)[^<]*(</span>)', r'\g<1>' + now + r'\g<2>', html)
    html = re.sub(r'(<span id="bn-chg">)[^<]*(</span>)', r'\g<1>' + str(changes_count) + r'\g<2>', html)
    html = re.sub(r'(<span id="bn-tot">)[^<]*(</span>)', r'\g<1>' + str(tools_count) + r'\g<2>', html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  ✓ index.html banner updated → {now}")


# ── WRITE DATA.JSON ──────────────────────────────────────────────
def write_data_json(all_tool_data: dict, all_changes: list, updated_ids: list):
    """Write data.json — this is what the HTML fetches to update itself."""
    now = fmt_ist()
    output = {
        "meta": {
            "updated":    now,
            "total":      TOTAL,
            "changes":    len(all_changes),
            "sections":   7,
            "generated":  now_ist().isoformat()
        },
        "updatedToday": updated_ids,
        "changes": all_changes,
        "tools": all_tool_data
    }
    with open("data.json", "w") as f:
        json.dump(output, f, indent=2)
    print(f"  ✓ data.json written → {TOTAL} tools, {len(all_changes)} changes")


# ── TELEGRAM ─────────────────────────────────────────────────────
def telegram(msg: str):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg[:4096], "parse_mode": "HTML"},
            timeout=12
        )
        print("  ✓ Telegram notification sent")
    except Exception as e:
        print(f"  ✗ Telegram failed: {e}")


# ── MAIN ─────────────────────────────────────────────────────────
def main():
    start = now_ist()
    print(f"\n{'═'*65}")
    print(f"  AI Tools Dashboard Auto-Updater")
    print(f"  Time    : {fmt_ist(start)}")
    print(f"  Model   : {NVIDIA_MODEL}")
    print(f"  Tools   : {TOTAL}")
    print(f"{'═'*65}\n")

    old_cache     = load_cache()
    new_cache     = {}
    all_tool_data = {}
    all_changes   = []
    updated_ids   = []

    for idx, tool in enumerate(TOOLS, 1):
        tid       = tool["id"]
        tname     = tool["name"]
        scrape_urls = tool["scrape_urls"]
        reddit_sub  = tool["reddit_sub"]
        reddit_q    = tool["reddit_q"]

        print(f"\n[{idx:02d}/{TOTAL}]  {tname}")
        new_cache[tid] = {"name": tname, "updated": start.isoformat()}
        tool_data      = {"lastScraped": fmt_ist(start), "sources": {}}
        tool_changed   = False

        # ── Scrape official pages ────────────────────────────────
        print(f"  Scraping {len(scrape_urls)} official page(s)...")
        page_text = scrape_multiple(scrape_urls, combined_max=7000)

        # Record scraped sources
        for url in scrape_urls:
            # Extract domain as source name
            domain = re.sub(r'https?://(www\.)?', '', url).split('/')[0]
            tool_data["sources"][domain] = url

        # ── Extract pricing plans ────────────────────────────────
        print(f"  → pricing plans    ", end="", flush=True)
        plans = extract_plans(tname, page_text)
        if plans:
            changed = has_changed(tid, "plans", plans, old_cache)
            if changed and tid in old_cache and "plans" in old_cache[tid]:
                all_changes.append({
                    "tool": tname,
                    "change": describe_change("plans", plans, old_cache[tid].get("plans", []))
                })
                tool_changed = True
            tool_data["plans"]  = plans
            new_cache[tid]["plans"] = plans
            print(f"✓ ({len(plans)} plans)")
        else:
            tool_data["plans"] = old_cache.get(tid, {}).get("plans", [])
            print("✗ (using cache)")
        time.sleep(2.5)

        # ── Extract free limits ──────────────────────────────────
        print(f"  → free limits      ", end="", flush=True)
        free = extract_free_limits(tname, page_text)
        if free:
            tool_data["free"]   = free
            new_cache[tid]["free"] = free
            print(f"✓ ({len(free)} items)")
        else:
            tool_data["free"] = old_cache.get(tid, {}).get("free", [])
            print("✗ (using cache)")
        time.sleep(2)

        # ── Extract usage limits ─────────────────────────────────
        print(f"  → usage limits     ", end="", flush=True)
        limits = extract_limits(tname, page_text)
        if limits:
            changed = has_changed(tid, "limits", limits, old_cache)
            if changed and tid in old_cache and "limits" in old_cache[tid]:
                all_changes.append({
                    "tool": tname,
                    "change": describe_change("limits", limits, old_cache[tid].get("limits", {}))
                })
                tool_changed = True
            tool_data["limits"]   = limits
            new_cache[tid]["limits"] = limits
            print(f"✓ ({len(limits)} items)")
        else:
            tool_data["limits"] = old_cache.get(tid, {}).get("limits", {})
            print("✗ (using cache)")
        time.sleep(2)

        # ── Extract features ────────────────────────────────────
        print(f"  → features         ", end="", flush=True)
        feats = extract_features(tname, page_text)
        if feats:
            tool_data["feats"]   = feats
            new_cache[tid]["feats"] = feats
            print(f"✓ ({len(feats)} features)")
        else:
            tool_data["feats"] = old_cache.get(tid, {}).get("feats", [])
            print("✗ (using cache)")
        time.sleep(2)

        # ── Research pros & cons ─────────────────────────────────
        print(f"  → pros & cons      ", end="", flush=True)
        pc = research_pros_cons(tname, page_text[:1500])
        if pc.get("pros") or pc.get("cons"):
            tool_data["pros"] = pc.get("pros", [])
            tool_data["cons"] = pc.get("cons", [])
            new_cache[tid]["pros"] = tool_data["pros"]
            new_cache[tid]["cons"] = tool_data["cons"]
            print(f"✓")
        else:
            tool_data["pros"] = old_cache.get(tid, {}).get("pros", [])
            tool_data["cons"] = old_cache.get(tid, {}).get("cons", [])
            print("✗ (using cache)")
        time.sleep(2)

        # ── Reddit community feedback ────────────────────────────
        print(f"  → reddit           ", end="", flush=True)
        reddit = fetch_reddit(tname, reddit_sub, reddit_q)
        if reddit:
            changed = has_changed(tid, "reddit", reddit, old_cache)
            if changed and tid in old_cache and "reddit" in old_cache[tid]:
                tool_changed = True
            tool_data["reddit"]   = reddit
            new_cache[tid]["reddit"] = reddit
            print(f"✓ ({len(reddit)} quotes)")
        else:
            tool_data["reddit"] = old_cache.get(tid, {}).get("reddit", [])
            print("✗ (using cache)")
        time.sleep(1.5)

        # ── Use cases (research once, cache indefinitely) ────────
        if tid not in old_cache or not old_cache[tid].get("uses"):
            print(f"  → use cases        ", end="", flush=True)
            uses = research_uses(tname)
            if uses:
                tool_data["uses"]   = uses
                new_cache[tid]["uses"] = uses
                print(f"✓ ({len(uses)} items)")
            else:
                print("✗")
            time.sleep(2)
        else:
            tool_data["uses"] = old_cache[tid]["uses"]
            new_cache[tid]["uses"] = tool_data["uses"]

        # Track if this tool had any changes
        if tool_changed:
            updated_ids.append(tid)

        all_tool_data[tid] = tool_data
        # Pause between tools to be respectful to rate limits
        time.sleep(2)

    # ── Save cache ───────────────────────────────────────────────
    save_cache(new_cache)

    # ── Write data.json (the live data source for HTML) ──────────
    write_data_json(all_tool_data, all_changes, updated_ids)

    # ── Update HTML banner ───────────────────────────────────────
    update_html_banner(len(all_changes), TOTAL)

    # ── Telegram notification ────────────────────────────────────
    today = fmt_ist()
    dash_url = f"https://{GITHUB_USER}.github.io/ai-tools-dashboard"

    if all_changes:
        # Group by tool
        by_tool: dict = {}
        for chg in all_changes:
            by_tool.setdefault(chg["tool"], []).append(chg["change"])

        lines = [
            f"<b>&#x1F6A8; AI Tools Dashboard Update</b>",
            f"<b>{today}</b>",
            f"\n<b>{len(updated_ids)} tool(s) with changes detected</b>\n"
        ]
        for tool_name, changes in list(by_tool.items())[:15]:
            lines.append(f"\n&#x1F504; <b>{tool_name}</b>")
            for c in changes[:3]:
                lines.append(f"  • {c}")

        lines.append(f"\n\n&#x1F4CA; <a href='{dash_url}'>View Dashboard</a>")
        telegram("\n".join(lines))
    else:
        telegram(
            f"&#x2705; <b>Daily Check Complete</b>\n"
            f"<b>{today}</b>\n\n"
            f"All <b>{TOTAL} tools</b> checked across 7 sections.\n"
            f"Sources scraped: {sum(len(t['scrape_urls']) for t in TOOLS)} pages\n"
            f"No pricing or feature changes detected today.\n\n"
            f"&#x1F4CA; <a href='{dash_url}'>Dashboard</a>"
        )

    # ── Summary ──────────────────────────────────────────────────
    end = now_ist()
    duration = int((end - start).total_seconds() / 60)
    print(f"\n{'═'*65}")
    print(f"  DONE")
    print(f"  Tools checked  : {TOTAL}")
    print(f"  Changes found  : {len(all_changes)}")
    print(f"  Tools updated  : {len(updated_ids)}")
    print(f"  Duration       : ~{duration} min")
    print(f"  Completed      : {fmt_ist(end)}")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
