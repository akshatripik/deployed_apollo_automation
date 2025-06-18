import os
import json
import joblib
from deep_translator import GoogleTranslator
from datetime import datetime
import time

# === Step 1: List and Select JSON File ===
json_files = sorted([f for f in os.listdir() if f.endswith('.json')])
if not json_files:
    print("❌ No JSON files found in the current directory.")
    exit()

print("\n📂 Available JSON files:")
for idx, file in enumerate(json_files):
    print(f"[{idx}] {file}")

try:
    selected_index = int(input("\n✏️ Enter the index of the input JSON file: ").strip())
    input_file = json_files[selected_index]
except (ValueError, IndexError):
    print("❌ Invalid selection.")
    exit()

print(f"\n✅ Selected file: {input_file}")

# === Step 2: Load JSON and ML Model ===
with open(input_file, 'r', encoding='utf-8') as f:
    raw_data = json.load(f)

print("\n📦 Loading model and vectorizer...")
model = joblib.load("relevance_rf_model.pkl")
vectorizer = joblib.load("translated_title_vectorizer.pkl")
translator = GoogleTranslator(source='auto', target='en')

# === Step 3: Handle Output Resume ===
output_json = "C_classified_titles.json"
final_entries = []
processed_ids = set()
start_index = 0

if os.path.exists(output_json):
    resume = input(f"\n📄 Output file '{output_json}' already exists. Do you want to continue from where it left off? (yes/no): ").strip().lower()
    if resume == "yes":
        with open(output_json, 'r', encoding='utf-8') as jf:
            final_entries = json.load(jf)
        processed_ids = {entry["id"] for entry in final_entries}
        raw_data = [entry for entry in raw_data if entry.get("id") not in processed_ids]
        start_index = len(final_entries)
        print(f"\n🔁 Resuming processing from entry {start_index + 1}. {len(raw_data)} new entries found.")
    else:
        print("⚠️ Starting fresh. Existing output file will be overwritten.")
        final_entries = []
else:
    print(f"🆕 Output file '{output_json}' will be created.")

# === Step 4: Translate, Score, and Save ===
total_entries = len(raw_data)
print(f"\n🌍 Translating & Scoring {total_entries} entries...\n")

with open(output_json, 'w', encoding='utf-8') as jf:
    for i, entry in enumerate(raw_data, start=start_index):
        title = entry.get("title", "")
        index_str = f"{i:05d}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry_no = f"[{i+1}/{start_index + total_entries}]"

        translated_title = ""
        score = "N/A"

        if not title or not isinstance(title, str) or title.strip() == "":
            log = f"{timestamp} {entry_no} ⏭️ | {score} | {translated_title} | {title}"
        else:
            try:
                try:
                    translated_title = translator.translate(title)
                except Exception:
                    time.sleep(1)
                    translated_title = translator.translate(title)

                vectorized = vectorizer.transform([translated_title])
                score = model.predict(vectorized)[0]
                log = f"{timestamp} {entry_no} ✅ | {score} | {translated_title} | {title}"
            except Exception as e:
                translated_title = "TRANSLATION_ERROR"
                score = "N/A"
                log = f"{timestamp} {entry_no} ❌ | {score} | ERROR | {title} — {e}"

        print(log)

        final_entry = {
            "index": index_str,
            "id": entry.get("id", ""),
            "title": title,
            "translated_title": translated_title,
            "relevance_score": str(score)
        }
        final_entries.append(final_entry)

        # Save progress incrementally
        jf.seek(0)
        json.dump(final_entries, jf, ensure_ascii=False, indent=2)
        jf.truncate()

print(f"\n💾 Translation complete. Output saved to: {output_json}")

# === Step 5: Retry Failed Translations ===
print("\n🔁 Retrying failed translations...\n")
retry_count = 0

for entry in final_entries:
    if entry["translated_title"] == "TRANSLATION_ERROR":
        try:
            translated_title = translator.translate(entry["title"])
            vectorized = vectorizer.transform([translated_title])
            score = model.predict(vectorized)[0]
            entry["translated_title"] = translated_title
            entry["relevance_score"] = str(score)
            retry_count += 1
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Index {entry['index']}] 🔁 RETRY SUCCESS | {score} | {translated_title}")
        except Exception as e:
            print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Index {entry['index']}] ❌ RETRY FAILED | {entry['title']} — {e}")

with open(output_json, 'w', encoding='utf-8') as jf:
    json.dump(final_entries, jf, ensure_ascii=False, indent=2)

print(f"\n✅ Retry complete. {retry_count} entries successfully re-translated.\n")

# === Step 6: Post-processing Keyword Matching ===
keywords = [
    "AUDIT", "AUDITOR", "AUDITING", "TAX", "TAXATION", "TAX ADVISOR",
    "LEGAL", "LAWYER", "ATTORNEY", "PARALEGAL", "ACCOUNT MANAGER", "CLIENT MANAGER",
    "RELATIONSHIP MANAGER", " HR ", "HR ", " HRBP ", "HRBP ", "HUMAN RESOURCE", "HUMAN CAPITAL",
    "TALENT MANAGEMENT", "KEY ACCOUNT MANAGER", "STRATEGIC ACCOUNT MANAGER",
    "ENTERPRISE ACCOUNT MANAGER", "MARKETING", " BRAND ", "PROMOTION",
    "DIGITAL MARKETING", " CONTENT ", "BUSINESS DEVELOPMENT", "BIZ DEV",
    " BD ", " BD ", "SALES", "SELLING", "SALES EXECUTIVE", "ACCOUNT EXECUTIVE",
    "TERRITORY MANAGER", "COMMERCIAL MANAGER", "COMMERCIAL LEAD", "TRADE MANAGER",
    "TALENT ACQUISITION", "RECRUITER", "HIRING MANAGER", "FINANCIAL", "FINANCE", "PUBLIC RELATIONS", "PUBLIC AFFAIRS",
    "TALENT", "COMMERCIAL", "CREDIT", "OFFICE"
]

print("🔍 Starting keyword matching...\n")
modified_count = 0

for entry in final_entries:
    translated_title = entry.get("translated_title", "").upper()
    matched = False
    for kw in keywords:
        if kw in translated_title:
            try:
                old_score = int(entry["relevance_score"])
                new_score = str(-old_score)
                print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Index {entry['index']}] ⚠️ Matched Keyword: '{kw}' | Title: '{entry['translated_title']}' | Old Score: {old_score} → New Score: {new_score}")
                entry["relevance_score"] = new_score
                modified_count += 1
                matched = True
                break
            except ValueError:
                break
    if not matched:
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} [Index {entry['index']}] ⏭️ No keyword match found.")

with open(output_json, 'w', encoding='utf-8') as jf:
    json.dump(final_entries, jf, ensure_ascii=False, indent=2)

print(f"\n✅ Keyword processing complete. {modified_count} entries updated in '{output_json}'")
