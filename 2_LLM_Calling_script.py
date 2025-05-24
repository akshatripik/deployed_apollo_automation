import json
import time
from collections import Counter
import google.generativeai as genai
from datetime import datetime
from pathlib import Path
import getpass
import os

# === CONFIGURATION ===
CLASSIFIED_OUTPUT_FILE = "C_classified_titles.json"
BATCH_SIZE = 3
MAX_RPD = 1500
MAX_RPM = 15  # Free-tier max RPM
SLEEP_TIME = 60 / MAX_RPM  # 4 seconds
RETRY_ATTEMPTS = 2

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
    files.sort()  # <-- Add this line to sort alphabetically
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
def classify_batch(titles, retry_attempts=RETRY_ATTEMPTS):
    prompt = f"""
You work for a Vision AI startup that builds AI agents to monitor equipment, materials, and processes in manufacturing industries like cement, steel, and metals.

Classify each job title as either **RELEVANT** or **NOT RELEVANT** for outreach.

**Instructions:**

1. Mark a title as **RELEVANT** only if:
   - The person is **white collar roles** **middle management or higher** (e.g. Inspector, Supervisor, Engineer, Manager, Head, VP, Director, CXO). Exclude interns, field workers or **blue-collar roles**. Focus only on **white-collar roles**.
   - The person works in one of the following relevant domains:

     - **Operations**: plant manager, operations, production, manufacturing head, shift incharge, 
     - **Maintenance**: maintenance, mechanical, electrical, technician, reliability
     - **Process**: process, optimization, optimisation  
     - **Quality**: quality, QA, QC, compliance  
     - **Safety**: safety, HSE, EHS  
     - **R&D**: R&D, research, development  
     - **Procurement**: procurement, purchase, buyer, sourcing  
     - **Projects**: project, capex, engineering manager  
     - **Automation**: automation, instrumentation, control systems  
     - **IT/Digital**: digital, IT, data, AI, ML, software, innovation  
     - **Leadership**: chief, CEO, COO, CTO, president, VP, director

2. Titles with clear **seniority** but **no department mentioned** are **RELEVANT** by default, as such roles often influence purchasing and digital adoption.

3. Titles from **irrelevant departments** (HR, Admin, Legal, Finance, Talent, Marketing) are **NOT RELEVANT**, even if senior.

4. Apply reasoning—don’t rely solely on keywords. For example, “Manager” is relevant, but “Finance Manager” is not.

5. Translate non-English titles before classification.

6. All titles that **end** with the word **analyst** are **NOT RELEVANT**.
**Output Format:**
Return a JSON list like:
[
  {{
    "original_title": "...",
    "translated_title": "...",
    "verdict": "RELEVANT" or "NOT RELEVANT"
  }},
  ...
]
Here are the titles:
{json.dumps(titles, ensure_ascii=False)}
"""
    for attempt in range(retry_attempts):
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
            err = str(e)
            if "429" in err:
                log("🚨 429 Rate limit hit. Sleeping 15s...")
                time.sleep(15)
            elif "504" in err or "Deadline Exceeded" in err:
                log(f"⚠️ 504 Timeout. Retrying in 10s... (Attempt {attempt+1}/{retry_attempts})")
                time.sleep(10)
            else:
                log(f"❌ Gemini API error: {e}")
                break
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

    time.sleep(SLEEP_TIME)  # Prevent 429
    results = classify_batch(titles)
    request_count += 1
    log(f"📡 Gemini API request #{request_count}")

    for j, result in enumerate(results):
        # Use zero-based index for the entry
        idx = len(classified_results)
        idx_str = f"{idx:05d}"
        id_ = ids[j]
        title = titles[j]
        translated = result.get("translated_title", "")
        verdict = result.get("verdict", "ERROR")
        classified_results.append({
            "index": idx_str,
            "id": id_,
            "title": title,
            "translated_title": translated,
            "classification": verdict
        })
        log(f"✅ {idx_str} | {verdict} | {translated} | {title}")
    entry_count += len(results)  # <-- Add this line

# === SAVE CLASSIFIED DATA ===
with open(CLASSIFIED_OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(classified_results, f, indent=2, ensure_ascii=False)

log("💾 Classification complete. Results saved to:")
print(f"📁 {Path(CLASSIFIED_OUTPUT_FILE).resolve()}")

log("📊 Summary:")
print(f"• Total entries processed  : {entry_count}")
print(f"• Total API requests made  : {request_count}")
print(f"• Output file              : {CLASSIFIED_OUTPUT_FILE}")
log("🏁 Done.")

# # === KEYWORD EXTRACTION ===
# def extract_keywords(results, label):
#     counter = Counter()
#     for item in results:
#         if item["classification"] == label:
#             tokens = item["title"].lower().replace("/", " ").replace("-", " ").split()
#             counter.update(tokens)
#     top_keywords = counter.most_common(20)
#     print(f"\n🔑 Top 20 {label} Keywords:")
#     for word, count in top_keywords:
#         print(f"{word} ({count})")
#     return [word for word, _ in top_keywords]

# include_keywords = extract_keywords(classified_results, "RELEVANT")
# exclude_keywords = extract_keywords(classified_results, "NOT RELEVANT")

# with open("include_keywords.txt", "w", encoding="utf-8") as f:
#     f.write("\n".join(include_keywords))

# with open("exclude_keywords.txt", "w", encoding="utf-8") as f:
#     f.write("\n".join(exclude_keywords))

# log("🏁 Done. Unified classification and keywords saved.")
