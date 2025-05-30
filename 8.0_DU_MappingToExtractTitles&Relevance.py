import os
import json
import csv
import random

# === Step 1: List all JSON files in the current directory ===
json_files = [f for f in os.listdir() if f.endswith('.json')]
json_files.sort()  # ✅ Sort alphabetically

if not json_files:
    print("❌ No JSON files found in the current directory.")
    exit()

print("\n📂 Available JSON files:")
for idx, file in enumerate(json_files):
    print(f"[{idx}] {file}")

# === Step 2: User selects files to merge ===
indices = input("\n✏️ Enter comma-separated index numbers of the files to merge: ").strip()
try:
    selected_indices = list(map(int, indices.split(',')))
except ValueError:
    print("❌ Invalid input. Please enter valid indices separated by commas.")
    exit()

# === Step 3: Merge and log entries from selected files ===
consolidated_entries = []
print("\n📊 Entry counts per file:")
for idx in selected_indices:
    file = json_files[idx]
    with open(file, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            print(f"❌ Error reading {file}, skipping.")
            continue
        if isinstance(data, dict):
            data = [data]
        print(f"  ✅ {file}: {len(data)} entries")
        consolidated_entries.extend(data)

# === Step 4: Jumble the entries ===
random.shuffle(consolidated_entries)

# === Step 5: Save to consolidated JSON and CSV ===
json_output = "consolidated_output.json"
csv_output = "consolidated_output.csv"

with open(json_output, 'w', encoding='utf-8') as f:
    json.dump(consolidated_entries, f, indent=2, ensure_ascii=False)

if consolidated_entries:
    keys = set()
    for entry in consolidated_entries:
        keys.update(entry.keys())
    keys = sorted(keys)

    with open(csv_output, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        for entry in consolidated_entries:
            writer.writerow({k: entry.get(k, '') for k in keys})

print(f"\n📦 Total entries in consolidated JSON and CSV: {len(consolidated_entries)}")
print(f"📝 Files created: {json_output}, {csv_output}")
