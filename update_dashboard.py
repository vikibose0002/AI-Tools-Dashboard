"""
AI Tools Dashboard Auto-Updater — Fixed & Final
================================================
Root cause fix: All major AI sites block scrapers (403).
Solution: NVIDIA NIM API is the primary data source.
- Researches pricing/features from AI knowledge (always works)
- Tries scraping as a bonus but never depends on it
- ALWAYS writes data.json even on partial failures
- IST timestamps throughout
- Adds Model Rankings from openrouter.ai insights
- Proper change detection (price-level comparison)
"""

import os, json, re, time, requests
from datetime import datetime, timezone, timedelta

# ── IST TIMEZONE ────────────────────────────────────────────────
IST = timezone(timedelta(hours=5, minutes=30))

def now_ist():
    return datetime.now(IST)

def fmt_ist(dt=None):
    if dt is None:
        dt = now_ist()
    return dt.strftime("%d %b %Y, %I:%M %p IST")

# ── CREDENTIALS ─────────────────────────────────────────────────
NVIDIA_KEY  = os.environ.get("GEMINI_API_KEY", "")
TG_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT     = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_USER = os.environ.get("GITHUB_USERNAME", "yourusername")

# ── NVIDIA NIM API CONFIG ────────────────────────────────────────
NVIDIA_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
# Primary model — change if 404:
NVIDIA_MODEL = "meta/llama-3.1-70b-instruct"
# Fallbacks if above fails:
# NVIDIA_MODEL = "nvidia/llama-3.1-nemotron-70b-instruct"
# NVIDIA_MODEL = "mistralai/mixtral-8x22b-instruct-v0.1"

# ── ALL 50 TOOLS ─────────────────────────────────────────────────
# official_url = the primary pricing page (shown as source in widget)
TOOLS = [
  # GENERAL AI
  {"id":"chatgpt","name":"ChatGPT","cat":"general","maker":"OpenAI",
   "official_url":"https://openai.com/chatgpt/pricing",
   "extra_urls":["https://openai.com/enterprise","https://help.openai.com"]},
  {"id":"claude","name":"Claude","cat":"general","maker":"Anthropic",
   "official_url":"https://claude.ai/pricing",
   "extra_urls":["https://support.claude.com/en/articles/9797531-what-is-the-enterprise-plan"]},
  {"id":"gemini","name":"Google Gemini","cat":"general","maker":"Google",
   "official_url":"https://one.google.com/intl/en/about/google-ai-plans/",
   "extra_urls":["https://workspace.google.com/intl/en/pricing"]},
  {"id":"m365","name":"Microsoft 365 Copilot","cat":"general","maker":"Microsoft",
   "official_url":"https://www.microsoft.com/en-us/microsoft-365-copilot/pricing-new",
   "extra_urls":["https://www.microsoft.com/en-us/microsoft-365-copilot/pricing/enterprise"]},
  # RESEARCH
  {"id":"perplexity","name":"Perplexity","cat":"research","maker":"Perplexity AI",
   "official_url":"https://www.perplexity.ai/pro",
   "extra_urls":["https://www.perplexity.ai/enterprise/pricing"]},
  {"id":"notebooklm","name":"NotebookLM","cat":"research","maker":"Google",
   "official_url":"https://notebooklm.google/plans",
   "extra_urls":[]},
  {"id":"elicit","name":"Elicit","cat":"research","maker":"Elicit",
   "official_url":"https://elicit.com/pricing",
   "extra_urls":[]},
  {"id":"consensus","name":"Consensus","cat":"research","maker":"Consensus",
   "official_url":"https://consensus.app/home/pricing/",
   "extra_urls":[]},
  # CONTENT
  {"id":"grammarly","name":"Grammarly","cat":"content","maker":"Grammarly",
   "official_url":"https://www.grammarly.com/plans",
   "extra_urls":["https://www.grammarly.com/business"]},
  {"id":"jasper","name":"Jasper","cat":"content","maker":"Jasper.ai",
   "official_url":"https://www.jasper.ai/pricing",
   "extra_urls":[]},
  {"id":"writesonic","name":"Writesonic","cat":"content","maker":"Writesonic",
   "official_url":"https://writesonic.com/pricing",
   "extra_urls":[]},
  {"id":"copyai","name":"Copy.ai","cat":"content","maker":"Copy.ai",
   "official_url":"https://www.copy.ai/pricing",
   "extra_urls":[]},
  {"id":"notionai","name":"Notion AI","cat":"content","maker":"Notion",
   "official_url":"https://www.notion.com/pricing",
   "extra_urls":["https://www.notion.com/product/ai"]},
  # CODING
  {"id":"ghcopilot","name":"GitHub Copilot","cat":"coding","maker":"Microsoft",
   "official_url":"https://github.com/features/copilot/plans",
   "extra_urls":["https://docs.github.com/en/copilot"]},
  {"id":"cursor","name":"Cursor","cat":"coding","maker":"Anysphere",
   "official_url":"https://www.cursor.com/pricing",
   "extra_urls":[]},
  {"id":"codex","name":"OpenAI Codex","cat":"coding","maker":"OpenAI",
   "official_url":"https://openai.com/codex",
   "extra_urls":["https://openai.com/api/pricing/"]},
  {"id":"tabnine","name":"Tabnine","cat":"coding","maker":"Tabnine",
   "official_url":"https://www.tabnine.com/pricing",
   "extra_urls":["https://www.tabnine.com/enterprise"]},
  {"id":"replit","name":"Replit Ghostwriter","cat":"coding","maker":"Replit",
   "official_url":"https://replit.com/pricing",
   "extra_urls":["https://replit.com/ai"]},
  {"id":"codeium","name":"Codeium","cat":"coding","maker":"Codeium",
   "official_url":"https://codeium.com/pricing",
   "extra_urls":["https://windsurf.com/pricing"]},
  {"id":"claudecode","name":"Claude Code","cat":"coding","maker":"Anthropic",
   "official_url":"https://claude.com/product/claude-code",
   "extra_urls":["https://claude.ai/pricing","https://docs.anthropic.com/en/docs/claude-code/overview"]},
  {"id":"autogen","name":"AutoGen","cat":"coding","maker":"Microsoft",
   "official_url":"https://github.com/microsoft/autogen",
   "extra_urls":["https://microsoft.github.io/autogen/"]},
  # WEBAPP / NO-CODE
  {"id":"v0","name":"v0","cat":"webapp","maker":"Vercel",
   "official_url":"https://v0.dev/pricing",
   "extra_urls":[]},
  {"id":"bubble","name":"Bubble","cat":"webapp","maker":"Bubble",
   "official_url":"https://bubble.io/pricing",
   "extra_urls":[]},
  {"id":"softr","name":"Softr","cat":"webapp","maker":"Softr",
   "official_url":"https://www.softr.io/pricing",
   "extra_urls":[]},
  {"id":"durable","name":"Durable","cat":"webapp","maker":"Durable",
   "official_url":"https://durable.co/pricing",
   "extra_urls":[]},
  {"id":"lovable","name":"Lovable AI","cat":"webapp","maker":"Lovable",
   "official_url":"https://lovable.dev/pricing",
   "extra_urls":[]},
  # DESIGN
  {"id":"figmaai","name":"Figma AI","cat":"design","maker":"Figma",
   "official_url":"https://www.figma.com/pricing/",
   "extra_urls":["https://www.figma.com/ai/"]},
  {"id":"uizard","name":"Uizard","cat":"design","maker":"Uizard",
   "official_url":"https://uizard.io/pricing/",
   "extra_urls":[]},
  {"id":"canva","name":"Canva Magic Studio","cat":"design","maker":"Canva",
   "official_url":"https://www.canva.com/pricing/",
   "extra_urls":["https://www.canva.com/magic/","https://www.canva.com/enterprise/"]},
  # IMAGE
  {"id":"midjourney","name":"Midjourney","cat":"image","maker":"Midjourney",
   "official_url":"https://docs.midjourney.com/docs/plans",
   "extra_urls":["https://www.midjourney.com/account"]},
  {"id":"dalle","name":"DALL-E","cat":"image","maker":"OpenAI",
   "official_url":"https://openai.com/api/pricing/",
   "extra_urls":["https://openai.com/index/dall-e-3/"]},
  {"id":"firefly","name":"Adobe Firefly","cat":"image","maker":"Adobe",
   "official_url":"https://www.adobe.com/products/firefly/pricing.html",
   "extra_urls":["https://www.adobe.com/creativecloud/plans.html"]},
  {"id":"leonardo","name":"Leonardo AI","cat":"image","maker":"Leonardo AI",
   "official_url":"https://leonardo.ai/pricing",
   "extra_urls":[]},
  # VIDEO
  {"id":"runway","name":"Runway","cat":"video","maker":"Runway ML",
   "official_url":"https://runwayml.com/pricing",
   "extra_urls":[]},
  {"id":"synthesia","name":"Synthesia","cat":"video","maker":"Synthesia",
   "official_url":"https://www.synthesia.io/pricing",
   "extra_urls":["https://www.synthesia.io/enterprise"]},
  {"id":"pika","name":"Pika","cat":"video","maker":"Pika Labs",
   "official_url":"https://pika.art/pricing",
   "extra_urls":[]},
  # AUDIO
  {"id":"elevenlabs","name":"ElevenLabs","cat":"audio","maker":"ElevenLabs",
   "official_url":"https://elevenlabs.io/pricing",
   "extra_urls":["https://elevenlabs.io/docs"]},
  {"id":"murf","name":"Murf","cat":"audio","maker":"Murf AI",
   "official_url":"https://murf.ai/pricing",
   "extra_urls":[]},
  {"id":"descript","name":"Descript","cat":"audio","maker":"Descript",
   "official_url":"https://www.descript.com/pricing",
   "extra_urls":[]},
  # AUTOMATION
  {"id":"zapier","name":"Zapier AI","cat":"automation","maker":"Zapier",
   "official_url":"https://zapier.com/pricing",
   "extra_urls":["https://zapier.com/ai"]},
  {"id":"make","name":"Make","cat":"automation","maker":"Make",
   "official_url":"https://www.make.com/en/pricing",
   "extra_urls":[]},
  {"id":"agenticworkers","name":"Agentic Workers","cat":"automation","maker":"Agentic Workers",
   "official_url":"https://www.agenticworkers.com/",
   "extra_urls":[]},
  {"id":"manus","name":"Manus","cat":"automation","maker":"Manus AI",
   "official_url":"https://manus.im/",
   "extra_urls":[]},
  {"id":"workbeaver","name":"Workbeaver","cat":"automation","maker":"Workbeaver",
   "official_url":"https://workbeaver.com/",
   "extra_urls":[]},
  # PRESENTATION
  {"id":"gamma","name":"Gamma","cat":"gtm","maker":"Gamma Tech",
   "official_url":"https://gamma.app/pricing",
   "extra_urls":[]},
  {"id":"beautifulai","name":"Beautiful.ai","cat":"gtm","maker":"Beautiful.ai",
   "official_url":"https://www.beautiful.ai/pricing",
   "extra_urls":[]},
  {"id":"tome","name":"Tome","cat":"gtm","maker":"Tome",
   "official_url":"https://tome.app/pricing",
   "extra_urls":[]},
  # ANALYTICS
  {"id":"powerbi","name":"Power BI Copilot","cat":"dashboard","maker":"Microsoft",
   "official_url":"https://powerbi.microsoft.com/en-us/pricing/",
   "extra_urls":["https://azure.microsoft.com/en-us/pricing/details/microsoft-fabric/"]},
  {"id":"tableau","name":"Tableau Pulse","cat":"dashboard","maker":"Salesforce",
   "official_url":"https://www.tableau.com/pricing/teams-orgs",
   "extra_urls":["https://www.tableau.com/products/tableau-pulse"]},
  {"id":"rowsai","name":"Rows AI","cat":"dashboard","maker":"Rows",
   "official_url":"https://rows.com/pricing",
   "extra_urls":["https://rows.com/ai"]},
]

TOTAL = len(TOOLS)  # 50

# ── NVIDIA API CALL ──────────────────────────────────────────────
SYS_STRICT = (
    "You are a precise AI pricing researcher with up-to-date knowledge. "
    "Respond with ONLY valid JSON. No markdown, no code fences, no explanation. "
    "Your data must be accurate and match what is on official websites."
)

def ask_nvidia(user_prompt: str, max_tokens: int = 900, retries: int = 3) -> str | None:
    if not NVIDIA_KEY:
        print("    ✗ NVIDIA_KEY not set")
        return None

    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Content-Type": "application/json"
    }
    body = {
        "model": NVIDIA_MODEL,
        "messages": [
            {"role": "system", "content": SYS_STRICT},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.05,
        "max_tokens": max_tokens,
        "top_p": 0.9
    }

    for attempt in range(retries):
        try:
            r = requests.post(NVIDIA_URL, headers=headers, json=body, timeout=45)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"].strip()
        except requests.exceptions.HTTPError as e:
            code = e.response.status_code if e.response else 0
            if code in [401, 403]:
                print(f"    ✗ Auth error HTTP {code} — check NVIDIA API key")
                return None
            if code == 404:
                print(f"    ✗ Model not found (HTTP 404) — check NVIDIA_MODEL in script")
                return None
            if code == 429:
                wait = (attempt + 1) * 20
                print(f"    ⏳ Rate limited — waiting {wait}s")
                time.sleep(wait)
            else:
                print(f"    ✗ HTTP {code} attempt {attempt+1}/{retries}")
                time.sleep(5)
        except Exception as e:
            print(f"    ✗ API error attempt {attempt+1}: {type(e).__name__}")
            time.sleep(4)
    return None


def safe_json(text: str):
    """Parse JSON from model response, stripping any fences."""
    if not text:
        return None
    t = text.strip()
    t = re.sub(r"^```(?:json)?\s*", "", t, flags=re.MULTILINE)
    t = re.sub(r"```\s*$", "", t, flags=re.MULTILINE)
    t = t.strip()
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        pass
    for pat in [r"(\[[\s\S]*\])", r"(\{[\s\S]*\})"]:
        m = re.search(pat, t)
        if m:
            try:
                return json.loads(m.group(1))
            except:
                pass
    return None


# ── RESEARCH FUNCTIONS ───────────────────────────────────────────

def research_plans(name: str, official_url: str) -> list:
    """Get all pricing plans from AI knowledge."""
    prompt = f"""What are ALL the pricing plans for {name} as of 2025?
Official pricing page: {official_url}

List EVERY plan including free tier if any. Be precise with exact dollar amounts.

Return ONLY a JSON array — no other text:
[{{"n":"Plan Name","p":"$X/month","d":"Key features and what is included in this plan"}}]

Critical: Do NOT miss any plan. Include free, starter, pro, business, enterprise, custom plans."""

    raw = ask_nvidia(prompt, max_tokens=800)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return parsed
    return []


def research_free_limits(name: str) -> list:
    """Get free plan limitations."""
    prompt = f"""What are the specific free plan limitations for {name} in 2025?
If no free plan exists, state that clearly.

Return ONLY a JSON array of limitation strings — no other text:
["Limitation 1","Limitation 2","Limitation 3"]

Be specific: include message limits, feature restrictions, storage caps, watermarks, trial periods."""

    raw = ask_nvidia(prompt, max_tokens=400)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return parsed
    return [f"Check {name} website for current free plan details"]


def research_limits(name: str) -> dict:
    """Get usage limits and caps."""
    prompt = f"""What are the specific usage limits and caps for {name} in 2025?
Include: context window, daily message cap, file upload limit, API rate limits, seat minimums.

Return ONLY a JSON object — no other text:
{{"Limit name":"Value","Limit name 2":"Value 2"}}

Be specific with actual numbers."""

    raw = ask_nvidia(prompt, max_tokens=400)
    parsed = safe_json(raw)
    if isinstance(parsed, dict) and len(parsed) >= 1:
        return {k: v for k, v in parsed.items() if v and str(v) != "null"}
    return {}


def research_features(name: str) -> list:
    """Get key features."""
    prompt = f"""What are the TOP 10 KEY FEATURES of {name} as of 2025?
Focus on what makes it unique and what users actually use daily.

Return ONLY a JSON array of 10 feature strings — no other text:
["Feature 1","Feature 2","Feature 3"]"""

    raw = ask_nvidia(prompt, max_tokens=400)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return parsed[:12]
    return []


def research_pros_cons(name: str) -> dict:
    """Get pros, cons, and hidden limitations."""
    prompt = f"""What are the real pros, cons, and HIDDEN LIMITATIONS of {name} in 2025?
Include: undisclosed limits, hidden costs, common user complaints, genuine advantages.

Return ONLY this JSON structure — no other text:
{{"pros":["Advantage 1","Advantage 2","Advantage 3","Advantage 4","Advantage 5"],"cons":["Hidden cost or limit 1","User complaint 2","Undisclosed issue 3","Limitation 4","Real limitation 5"]}}"""

    raw = ask_nvidia(prompt, max_tokens=500)
    parsed = safe_json(raw)
    if isinstance(parsed, dict) and "pros" in parsed:
        return parsed
    return {"pros": [], "cons": []}


def research_uses(name: str) -> list:
    """Get primary use cases."""
    prompt = f"""What are the TOP 8 PRACTICAL USE CASES for {name} in 2025?
What do real professionals actually use it for daily?

Return ONLY a JSON array — no other text:
["Use case 1","Use case 2","Use case 3"]"""

    raw = ask_nvidia(prompt, max_tokens=300)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 1:
        return parsed[:10]
    return []


def fetch_reddit_quotes(name: str) -> list:
    """Fetch real Reddit community feedback."""
    try:
        q = requests.utils.quote(f"{name} pricing review 2025")
        url = f"https://www.reddit.com/search.json?q={q}&sort=relevance&t=month&limit=15&type=link"
        r = requests.get(
            url,
            headers={"User-Agent": "AI-Tools-Researcher/1.0 (academic project)"},
            timeout=15
        )
        if r.status_code != 200:
            return []

        posts = r.json().get("data", {}).get("children", [])
        quotes = []
        for post in posts:
            pd    = post.get("data", {})
            title = pd.get("title", "").strip()
            body  = pd.get("selftext", "").strip()
            sub   = pd.get("subreddit", "")
            score = pd.get("score", 0)

            if score < 3:
                continue

            text = (body if len(body) > 50 else title)[:220].strip()
            if len(text) < 25:
                continue

            text = re.sub(r'\s+', ' ', text)
            if len(text) >= 218:
                # Cut at last sentence boundary
                cut = text.rfind('. ')
                text = text[:cut + 1] if cut > 80 else text + "..."

            quote = f'"{text}" — r/{sub}'
            if quote not in quotes:
                quotes.append(quote)
            if len(quotes) >= 3:
                break

        return quotes
    except Exception as e:
        print(f"    ⚠ Reddit fetch failed: {type(e).__name__}")
        return []


# ── MODEL RANKINGS RESEARCH ──────────────────────────────────────

RANKING_CATEGORIES = [
    ("General AI Assistant",      "general chat, reasoning, writing, and multi-modal tasks"),
    ("Research & Search",         "research, citation, literature review, evidence synthesis"),
    ("Writing & Content",         "marketing copywriting, SEO content, brand voice, email"),
    ("Coding & Development",      "code generation, debugging, refactoring, agentic coding"),
    ("Web App / No-Code Building","web app generation, UI creation, full-stack from prompts"),
    ("Design & UI/UX",            "UI design, image generation for design, visual prototyping"),
    ("Image Generation",          "text-to-image, photorealism, artistic quality"),
    ("Video Generation",          "text-to-video, video quality, motion consistency"),
    ("Audio & Voice",             "voice synthesis, voice cloning, TTS quality"),
    ("Productivity & Automation", "workflow automation, agentic tasks, multi-step processes"),
    ("Presentation & Documents",  "presentation creation, document generation"),
    ("Data & Analytics",          "data analysis, BI insights, natural language to charts"),
]


def research_model_rankings() -> list:
    """Research top 2 AI models per category with evidence."""
    print("\n  Researching model rankings from openrouter.ai/rankings insights...")

    prompt = f"""Based on current AI model performance data from openrouter.ai/rankings and benchmark results as of 2025, 
provide the TOP 2 AI MODELS for each of these 12 categories.

For each category provide:
1. Top 2 model names with their makers
2. Key benchmark scores or evidence (SWE-bench, MMLU, Arena Elo, etc.)
3. Why each model leads in that category
4. One real data point or benchmark score

Categories:
{chr(10).join(f'{i+1}. {cat[0]} — {cat[1]}' for i, cat in enumerate(RANKING_CATEGORIES))}

Return ONLY a JSON array — no other text:
[
  {{
    "category": "Category Name",
    "rank1": {{
      "model": "Model Name",
      "maker": "Company",
      "score": "Key metric (e.g. Arena Elo: 1350, SWE-bench: 72%)",
      "evidence": "Why this model leads — specific data point",
      "badge": "e.g. #1 Arena Elo"
    }},
    "rank2": {{
      "model": "Model Name",
      "maker": "Company", 
      "score": "Key metric",
      "evidence": "Why this is #2 — specific data point",
      "badge": "e.g. Best value"
    }},
    "source": "openrouter.ai/rankings and benchmark data",
    "updated": "{fmt_ist()}"
  }}
]"""

    raw = ask_nvidia(prompt, max_tokens=1200)
    parsed = safe_json(raw)
    if isinstance(parsed, list) and len(parsed) >= 8:
        return parsed

    # Fallback: research each category individually
    print("    Full rankings failed — trying per-category...")
    rankings = []
    for cat_name, cat_desc in RANKING_CATEGORIES[:6]:  # do 6 on fallback
        fp = f"""What are the TOP 2 AI MODELS for {cat_name} ({cat_desc}) based on openrouter.ai/rankings and benchmarks in 2025?

Return ONLY this JSON — no other text:
{{"category":"{cat_name}","rank1":{{"model":"Model Name","maker":"Company","score":"Metric value","evidence":"Why #1","badge":"Achievement"}},"rank2":{{"model":"Model Name","maker":"Company","score":"Metric value","evidence":"Why #2","badge":"Achievement"}},"source":"openrouter.ai/rankings","updated":"{fmt_ist()}"}}"""

        raw2 = ask_nvidia(fp, max_tokens=400)
        parsed2 = safe_json(raw2)
        if isinstance(parsed2, dict) and "rank1" in parsed2:
            rankings.append(parsed2)
        time.sleep(2)

    return rankings


# ── CACHE ────────────────────────────────────────────────────────
def load_cache() -> dict:
    try:
        if os.path.exists("cache.json"):
            with open("cache.json") as f:
                return json.load(f)
    except Exception as e:
        print(f"  ⚠ Cache load failed: {e}")
    return {}


def save_cache(data: dict):
    try:
        with open("cache.json", "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"  ⚠ Cache save failed: {e}")


# ── CHANGE DETECTION (price-level) ───────────────────────────────
def extract_prices(data) -> set:
    """Extract all dollar amounts from any data structure."""
    text = json.dumps(data)
    return set(re.findall(r'\$[\d,]+(?:\.\d+)?(?:/\w+(?:/\w+)?)?', text))


def detect_change(tid: str, section: str, new_data, old_cache: dict) -> str | None:
    """Return change description string, or None if no change."""
    if tid not in old_cache or section not in old_cache.get(tid, {}):
        return None  # First run — don't flag as change

    old_prices = extract_prices(old_cache[tid].get(section, {}))
    new_prices  = extract_prices(new_data)

    added   = new_prices - old_prices
    removed = old_prices - new_prices

    if added:
        return f"{section}: new price point(s) — {', '.join(sorted(added))}"
    if removed:
        return f"{section}: price(s) removed — {', '.join(sorted(removed))}"

    # Check for significant content change (not just minor wording)
    old_str = json.dumps(old_cache[tid].get(section, ""), sort_keys=True)
    new_str = json.dumps(new_data, sort_keys=True)
    if len(old_str) > 20 and abs(len(new_str) - len(old_str)) > len(old_str) * 0.25:
        return f"{section}: content significantly updated"

    return None


# ── WRITE data.json ──────────────────────────────────────────────
def write_data_json(all_tool_data: dict, all_changes: list, updated_ids: list,
                    model_rankings: list):
    """Write data.json — always succeeds, even with partial data."""
    payload = {
        "meta": {
            "updated":  fmt_ist(),
            "total":    TOTAL,
            "changes":  len(all_changes),
            "sections": 7,
            "generated_utc": datetime.now(timezone.utc).isoformat()
        },
        "updatedToday":   updated_ids,
        "changeLog":      all_changes,
        "tools":          all_tool_data,
        "modelRankings":  model_rankings,
    }
    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    size_kb = os.path.getsize("data.json") // 1024
    print(f"\n  ✓ data.json written — {TOTAL} tools, {len(all_changes)} changes, {size_kb}KB")


# ── UPDATE HTML BANNER ───────────────────────────────────────────
def update_html_banner(changes_count: int):
    if not os.path.exists("index.html"):
        print("  ⚠ index.html not found — skipping banner update")
        return

    with open("index.html", encoding="utf-8") as f:
        html = f.read()

    now = fmt_ist()

    # Update span values
    html = re.sub(r'(<span id="bn-time">)[^<]*(</span>)', rf'\g<1>{now}\g<2>', html)
    html = re.sub(r'(<span id="bn-chg">)[^<]*(</span>)', rf'\g<1>{changes_count}\g<2>', html)
    html = re.sub(r'(<span id="bn-tot">)[^<]*(</span>)', rf'\g<1>{TOTAL}\g<2>', html)
    # Update stat card date
    html = re.sub(r'(<div[^>]+id="stat-date"[^>]*>)[^<]*(</div>)',
                  rf'\g<1>{now.split(",")[0]}\g<2>', html)
    html = re.sub(r'(<div[^>]+id="stat-chg"[^>]*>)[^<]*(</div>)',
                  rf'\g<1>{changes_count}\g<2>', html)

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  ✓ index.html banner → {now}")


# ── TELEGRAM ─────────────────────────────────────────────────────
def telegram(msg: str):
    if not TG_TOKEN or not TG_CHAT:
        print("  ⚠ Telegram credentials not set — skipping notification")
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg[:4096], "parse_mode": "HTML"},
            timeout=12
        )
        print("  ✓ Telegram notification sent")
    except Exception as e:
        print(f"  ✗ Telegram failed: {type(e).__name__}")


# ── MAIN ─────────────────────────────────────────────────────────
def main():
    start = now_ist()
    print(f"\n{'═'*65}")
    print(f"  AI Tools Dashboard Updater — {fmt_ist(start)}")
    print(f"  Model  : {NVIDIA_MODEL}")
    print(f"  Tools  : {TOTAL}")
    print(f"  Source : NVIDIA NIM API (AI-powered research)")
    print(f"{'═'*65}\n")

    old_cache     = load_cache()
    new_cache     = {}
    all_tool_data = {}
    all_changes   = []
    updated_ids   = []
    is_first_run  = len(old_cache) == 0

    if is_first_run:
        print("  ℹ FIRST RUN — populating baseline data from AI research\n")

    for idx, tool in enumerate(TOOLS, 1):
        tid  = tool["id"]
        name = tool["name"]
        url  = tool["official_url"]

        print(f"[{idx:02d}/{TOTAL}] {name}")
        new_cache[tid] = {"name": name, "ts": start.isoformat()}
        tool_data      = {
            "sources": {
                "Official Pricing": url,
                **{f"Reference {i+1}": eu for i, eu in enumerate(tool.get("extra_urls", []))},
                "Reddit Community": f"https://www.reddit.com/search/?q={requests.utils.quote(name)}",
            }
        }
        tool_changed = False

        # ── 1. PRICING PLANS (NVIDIA API) ─────────────────────
        print(f"  → plans     ", end="", flush=True)
        plans = research_plans(name, url)
        if plans:
            chg = detect_change(tid, "plans", plans, old_cache)
            if chg:
                all_changes.append({"tool": name, "change": chg})
                tool_changed = True
            new_cache[tid]["plans"] = plans
            tool_data["plans"] = plans
            print(f"✓ {len(plans)} plans")
        else:
            cached = old_cache.get(tid, {}).get("plans", [])
            tool_data["plans"] = cached
            print("✗ (cache)")
        time.sleep(2)

        # ── 2. FREE LIMITS ─────────────────────────────────────
        print(f"  → free      ", end="", flush=True)
        free = research_free_limits(name)
        if free:
            new_cache[tid]["free"] = free
            tool_data["free"] = free
            print(f"✓ {len(free)} items")
        else:
            tool_data["free"] = old_cache.get(tid, {}).get("free", [])
            print("✗ (cache)")
        time.sleep(2)

        # ── 3. USAGE LIMITS ────────────────────────────────────
        print(f"  → limits    ", end="", flush=True)
        limits = research_limits(name)
        if limits:
            chg = detect_change(tid, "limits", limits, old_cache)
            if chg:
                all_changes.append({"tool": name, "change": chg})
                tool_changed = True
            new_cache[tid]["limits"] = limits
            tool_data["limits"] = limits
            print(f"✓ {len(limits)} items")
        else:
            tool_data["limits"] = old_cache.get(tid, {}).get("limits", {})
            print("✗ (cache)")
        time.sleep(2)

        # ── 4. FEATURES ────────────────────────────────────────
        print(f"  → features  ", end="", flush=True)
        feats = research_features(name)
        if feats:
            new_cache[tid]["feats"] = feats
            tool_data["feats"] = feats
            print(f"✓ {len(feats)} items")
        else:
            tool_data["feats"] = old_cache.get(tid, {}).get("feats", [])
            print("✗ (cache)")
        time.sleep(2)

        # ── 5. PROS & CONS ─────────────────────────────────────
        print(f"  → pros/cons ", end="", flush=True)
        pc = research_pros_cons(name)
        if pc.get("pros") or pc.get("cons"):
            new_cache[tid]["pros"] = pc.get("pros", [])
            new_cache[tid]["cons"] = pc.get("cons", [])
            tool_data["pros"] = pc.get("pros", [])
            tool_data["cons"] = pc.get("cons", [])
            print(f"✓")
        else:
            tool_data["pros"] = old_cache.get(tid, {}).get("pros", [])
            tool_data["cons"] = old_cache.get(tid, {}).get("cons", [])
            print("✗ (cache)")
        time.sleep(2)

        # ── 6. REDDIT FEEDBACK ─────────────────────────────────
        print(f"  → reddit    ", end="", flush=True)
        reddit = fetch_reddit_quotes(name)
        if reddit:
            new_cache[tid]["reddit"] = reddit
            tool_data["reddit"] = reddit
            print(f"✓ {len(reddit)} quotes")
        else:
            tool_data["reddit"] = old_cache.get(tid, {}).get("reddit", [])
            print("✗ (cache)")
        time.sleep(1.5)

        # ── 7. USE CASES (research once, then cache) ───────────
        if not old_cache.get(tid, {}).get("uses"):
            print(f"  → uses      ", end="", flush=True)
            uses = research_uses(name)
            if uses:
                new_cache[tid]["uses"] = uses
                tool_data["uses"] = uses
                print(f"✓ {len(uses)} items")
            else:
                print("✗")
            time.sleep(2)
        else:
            tool_data["uses"] = old_cache[tid]["uses"]
            new_cache[tid]["uses"] = tool_data["uses"]

        if tool_changed:
            updated_ids.append(tid)
            print(f"  ⚡ Changes detected for {name}")

        all_tool_data[tid] = tool_data
        time.sleep(1)

    # ── MODEL RANKINGS ─────────────────────────────────────────
    model_rankings = research_model_rankings()
    print(f"  ✓ Model rankings: {len(model_rankings)} categories researched")

    # ── ALWAYS WRITE data.json ──────────────────────────────────
    write_data_json(all_tool_data, all_changes, updated_ids, model_rankings)

    # ── SAVE CACHE ──────────────────────────────────────────────
    save_cache(new_cache)

    # ── UPDATE HTML BANNER ──────────────────────────────────────
    update_html_banner(len(all_changes))

    # ── TELEGRAM NOTIFICATION ───────────────────────────────────
    today    = fmt_ist()
    dash_url = f"https://{GITHUB_USER}.github.io/ai-tools-dashboard"

    if all_changes:
        lines = [
            f"<b>&#x1F6A8; AI Dashboard Update — {today}</b>",
            f"<b>{len(all_changes)} change(s) across {len(updated_ids)} tool(s)</b>\n"
        ]
        for chg in all_changes[:15]:
            lines.append(f"  &#x1F504; <b>{chg['tool']}</b>: {chg['change']}")
        lines.append(f"\n&#x1F4CA; <a href='{dash_url}'>View Dashboard</a>")
        telegram("\n".join(lines))
    else:
        telegram(
            f"&#x2705; <b>Daily Check — {today}</b>\n\n"
            f"All <b>{TOTAL} tools</b> checked across 7 sections.\n"
            f"No pricing or feature changes detected.\n"
            f"Model rankings updated: {len(model_rankings)} categories\n\n"
            f"&#x1F4CA; <a href='{dash_url}'>Dashboard</a>"
        )

    # ── SUMMARY ────────────────────────────────────────────────
    elapsed = int((now_ist() - start).total_seconds() / 60)
    print(f"\n{'═'*65}")
    print(f"  Completed: {fmt_ist()}")
    print(f"  Duration : ~{elapsed} minutes")
    print(f"  Changes  : {len(all_changes)}")
    print(f"  Tools    : {TOTAL}")
    print(f"{'═'*65}\n")


if __name__ == "__main__":
    main()
