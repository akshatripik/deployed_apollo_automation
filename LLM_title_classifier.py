import json
import time
from collections import Counter
import google.generativeai as genai
from datetime import datetime
from pathlib import Path
import getpass
import os

# === CONFIGURATION ===
CLASSIFIED_OUTPUT_FILE = "classified_titles.json"
BATCH_SIZE = 3
MAX_RPD = 1500
MAX_RPM = 30
SLEEP_TIME = 60 / MAX_RPM  # 2 seconds between API calls

# === GET API KEY ===
API_KEY = getpass.getpass("🔐 Enter your Gemini API Key: ").strip()
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# === LOG FUNCTION ===
def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

# === LIST JSON FILES ===
def list_json_files():
    files = [f for f in os.listdir('.') if f.endswith('.json')]
    if not files:
        print("❌ No JSON files found in this directory.")
        exit()
    print("📂 Available JSON files:")
    for idx, fname in enumerate(files):
        print(f"{idx:02d}. {fname}")
    return files

# === PROMPT FOR FILE SELECTION ===
def select_file():
    json_files = list_json_files()
    choice = input("🔢 Enter the number of the file to process: ").strip()
    try:
        index = int(choice)
        return json_files[index]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        exit()

# === LOAD INPUT ===
input_file = select_file()
try:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert isinstance(data, list), "Input must be a list of dicts with 'id' and 'title'"
    log(f"📊 Loaded {len(data)} entries from {input_file}")
except Exception as e:
    log(f"🛑 Failed to load JSON: {e}")
    raise SystemExit

# === GEMINI CLASSIFICATION ===
def classify_batch(titles):
    prompt = f"""
You are an assistant working for a Vision AI startup that builds AI agents to monitor equipment, materials, and processes in large manufacturing industries such as cement, steel, and metal production.

We want to classify each of the job titles provided below as either **RELEVANT** or **NOT RELEVANT** for outreach purposes.

**Instructions:**

1. Classify a title as **RELEVANT** only if:
   - The title indicates the person holds **middle management or higher** authority (e.g., Manager, Head, VP, Director, CXO). Do **not** include entry-level roles, field workers, or interns.
   - The person works in one of the following **functional domains**, which align with KPIs that our Vision AI product helps improve:
     - Process Engineering / Process Optimization
     - Product Engineering / Product Development
     - Melt Shop / Steel Shop / Furnace Operations (in steel and metal industries)
     - Maintenance (Mechanical / Electrical / Instrumentation)
     - Plant / Factory / Site Safety
     - Digitization / Digital Factory / Industry 4.0

2. Use your **reasoning ability** to evaluate the title holistically. **Do not rely solely on keyword matching.** For example, if a title contains the word "manager" but belongs to HR or Marketing, it may still be **NOT RELEVANT**.

3. If the title is in a non-English language, translate it into English.

Return JSON list with this format:
[
  {{
    "original_title": "...",
    "translated_title": "...",
    "verdict": "RELEVANT" or "NOT RELEVANT"
  }},
  ...
]

Titles:
{json.dumps(titles, ensure_ascii=False)}
"""
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        if not raw:
            raise ValueError("Empty response from Gemini.")

        first_bracket = raw.find("[")
        last_bracket = raw.rfind("]") + 1
        if first_bracket == -1 or last_bracket == -1:
            raise ValueError("No JSON structure found in response.")

        json_text = raw[first_bracket:last_bracket]
        return json.loads(json_text)

    except Exception as e:
        log(f"❌ Gemini API error: {e}")
        return [{"original_title": t, "translated_title": "", "verdict": "ERROR"} for t in titles]

# === PROCESSING ===
classified_results = []
request_count = 0
entry_count = 0

log(f"🔍 Starting classification in batches of {BATCH_SIZE}...")

for i in range(0, len(data), BATCH_SIZE):
    if request_count >= MAX_RPD:
        log("🛑 Max daily request limit (1500) reached. Stopping.")
        break

    batch = data[i:i+BATCH_SIZE]
    titles = [entry['title'] for entry in batch]
    ids = [entry['id'] for entry in batch]

    results = classify_batch(titles)
    request_count += 1
    log(f"📡 Gemini API request #{request_count}")

    for j, result in enumerate(results):
        entry_count += 1
        id_ = ids[j]
        title = titles[j]
        translated = result.get("translated_title", "")
        verdict = result.get("verdict", "ERROR")

        classified_results.append({
            "id": id_,
            "title": title,
            "translated_title": translated,
            "classification": verdict
        })

        log(f"✅ {entry_count}/{len(data)} | {verdict} | {title}")
    time.sleep(SLEEP_TIME)

# === SAVE CLASSIFIED DATA ===
with open(CLASSIFIED_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(classified_results, f, indent=2, ensure_ascii=False)

# === KEYWORD EXTRACTION ===
def extract_keywords(results, label):
    counter = Counter()
    for item in results:
        if item["classification"] == label:
            tokens = item["title"].lower().replace("/", " ").replace("-", " ").split()
            counter.update(tokens)
    top_keywords = counter.most_common(20)
    print(f"\n🔑 Top 20 {label} Keywords:")
    for word, count in top_keywords:
        print(f"{word} ({count})")
    return [word for word, _ in top_keywords]

include_keywords = extract_keywords(classified_results, "RELEVANT")
exclude_keywords = extract_keywords(classified_results, "NOT RELEVANT")

with open("include_keywords.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(include_keywords))

with open("exclude_keywords.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(exclude_keywords))

log("🏁 Done. Unified classification and keywords saved.")
