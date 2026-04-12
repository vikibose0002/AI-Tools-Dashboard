import os, json, requests, re
from datetime import datetime

GEMINI_KEY = os.environ[AIzaSyDhjw6BCaCP450eH2OBPOGHb_3kOAP3raw]
TG_TOKEN   = os.environ['TELEGRAM_BOT_TOKEN']
TG_CHAT    = os.environ['TELEGRAM_CHAT_ID']

TOOLS = [
    ("chatgpt",    "ChatGPT",            "ChatGPT Plus Pro Business Enterprise pricing 2025"),
    ("claude",     "Claude",             "Anthropic Claude Pro Max Team Enterprise pricing 2025"),
    ("gemini",     "Google Gemini",      "Google Gemini AI Pro Ultra Workspace pricing 2025"),
    ("m365",       "M365 Copilot",       "Microsoft 365 Copilot Business Enterprise pricing 2025"),
    ("perplexity", "Perplexity AI",      "Perplexity Pro Enterprise Max pricing 2025"),
    ("gamma",      "Gamma",              "Gamma app Plus Pro Team Business pricing 2025"),
    ("canva",      "Canva",              "Canva Pro Teams Enterprise pricing 2025"),
    ("cursor",     "Cursor",             "Cursor AI Pro Teams pricing 2025"),
    ("ghcopilot",  "GitHub Copilot",     "GitHub Copilot Individual Business Enterprise pricing 2025"),
    ("midjourney", "Midjourney",         "Midjourney Basic Standard Pro Mega pricing 2025"),
    ("elevenlabs", "ElevenLabs",         "ElevenLabs Starter Creator Pro Scale pricing 2025"),
    ("runway",     "Runway ML",          "Runway ML Standard Pro Unlimited pricing 2025"),
    ("lovable",    "Lovable AI",         "Lovable AI Starter Pro Business pricing 2025"),
    ("v0",         "v0 by Vercel",       "v0 Vercel Premium Team Business pricing 2025"),
    ("jasper",     "Jasper AI",          "Jasper AI Creator Pro Business pricing 2025"),
    ("powerbi",    "Power BI",           "Microsoft Power BI Pro Premium pricing 2025"),
    ("zapier",     "Zapier",             "Zapier Starter Professional Team pricing 2025"),
    ("notebooklm", "NotebookLM",         "Google NotebookLM Plus pricing 2025"),
    ("tableau",    "Tableau",            "Tableau Viewer Explorer Creator pricing 2025"),
]

def ask_gemini(question):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    body = {
        "contents": [{"parts": [{"text":
            f"You are an AI pricing researcher. Answer this with only current factual pricing data, be concise:\n\n{question}"
        }]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 400}
    }
    try:
        r = requests.post(url, json=body, timeout=20)
        r.raise_for_status()
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def load_cache():
    if os.path.exists('cache.json'):
        with open('cache.json') as f:
            return json.load(f)
    return {}

def save_cache(data):
    with open('cache.json', 'w') as f:
        json.dump(data, f, indent=2)

def find_changes(tid, new_text, cache):
    if tid not in cache:
        return []
    old = cache[tid].get('info', '')
    old_prices = set(re.findall(r'\$[\d,.]+', old))
    new_prices = set(re.findall(r'\$[\d,.]+', new_text))
    changes = []
    added = new_prices - old_prices
    removed = old_prices - new_prices
    if added:
        changes.append(f"New prices: {', '.join(sorted(added))}")
    if removed:
        changes.append(f"Removed prices: {', '.join(sorted(removed))}")
    for kw in ['discontinued','new plan','free tier','launched','increased','decreased']:
        if kw in new_text.lower() and kw not in old.lower():
            changes.append(f"Keyword alert: '{kw}'")
    return changes

def telegram(msg):
    try:
        requests.post(
            f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage",
            json={"chat_id": TG_CHAT, "text": msg, "parse_mode": "HTML"},
            timeout=10
        )
        print("Telegram sent")
    except Exception as e:
        print(f"Telegram failed: {e}")

def update_html(changes_count):
    if not os.path.exists('index.html'):
        return
    with open('index.html', encoding='utf-8') as f:
        html = f.read()
    now = datetime.now().strftime("%d %b %Y, %I:%M %p")
    banner = f'''<div id="auto-banner" style="background:#f0fdf4;border:1px solid #86efac;
border-radius:8px;padding:10px 16px;margin-bottom:14px;font-size:12px;color:#166534;
font-family:Inter,sans-serif;">
&#x1F504; <strong>Auto-updated:</strong> {now} &nbsp;|&nbsp;
<strong>Changes today:</strong> {changes_count} &nbsp;|&nbsp;
<strong>Tools tracked:</strong> {len(TOOLS)}
</div>'''
    html = re.sub(r'<div id="auto-banner".*?</div>', '', html, flags=re.DOTALL)
    html = html.replace('<div class="stat-row">', banner + '\n<div class="stat-row">', 1)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("HTML updated")

def check_new_tools():
    result = ask_gemini("List 3 brand new AI tools launched in the last 30 days that are useful for marketing, coding, or productivity. Just tool name and one line description.")
    return result or ""

def main():
    print(f"Running — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    cache = load_cache()
    new_cache = {}
    all_changes = []

    for tid, name, query in TOOLS:
        print(f"Checking {name}...")
        info = ask_gemini(query)
        if not info:
            continue
        new_cache[tid] = {"name": name, "info": info, "at": datetime.now().isoformat()}
        changes = find_changes(tid, info, cache)
        if changes:
            all_changes.append({"tool": name, "changes": changes})
            print(f"  CHANGED: {changes}")

    new_tools_text = check_new_tools()
    save_cache(new_cache)
    update_html(len(all_changes))

    today = datetime.now().strftime("%d %b %Y")

    if all_changes:
        lines = [f"<b>&#x1F6A8; AI Tools Update — {today}</b>\n"]
        for item in all_changes:
            lines.append(f"\n&#x1F504; <b>{item['tool']}</b>")
            for c in item['changes']:
                lines.append(f"  • {c}")
        if new_tools_text:
            lines.append(f"\n\n&#x1F195; <b>New Tools This Month:</b>\n{new_tools_text[:400]}")
        lines.append(f"\n\n&#x1F4CA; Dashboard: https://yourusername.github.io/ai-tools-dashboard")
        telegram("\n".join(lines))
    else:
        telegram(
            f"&#x2705; <b>Daily Check — {today}</b>\n\n"
            f"No changes across {len(TOOLS)} tools.\n"
            f"Dashboard is current.\n\n"
            f"&#x1F195; New tools check:\n{new_tools_text[:300] if new_tools_text else 'Nothing notable'}\n\n"
            f"&#x1F4CA; https://vikibose0002.github.io/ai-tools-dashboard"
        )

if __name__ == "__main__":
    main()
