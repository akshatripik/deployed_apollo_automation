import json
import csv
import os

# === Ask for JSON filename ===
json_filename = input("📄 Enter the JSON filename (e.g., data.json): ").strip()

# Check if file exists in the same folder
if not os.path.exists(json_filename):
    print(f"❌ File '{json_filename}' not found in current directory.")
    exit()

# === Load JSON data ===
with open(json_filename, 'r', encoding='utf-8') as f:
    data = json.load(f)

# === Flatten into rows for CSV ===
rows = []
for person in data:
    employment_history = person.get("employment_history", [])
    for job in employment_history:
        row = {
            "id": person.get("id"),
            "first_name": person.get("first_name"),
            "last_name": person.get("last_name"),
            "title": person.get("title"),
            "linkedin_url": person.get("linkedin_url"),
            "city": person.get("city"),
            "state": person.get("state"),
            "country": person.get("country"),
            "employment_title": job.get("title"),
            "employment_org": job.get("organization_name"),
            "start_date": job.get("start_date"),
            "end_date": job.get("end_date"),
            "is_current": job.get("current")
        }
        rows.append(row)

# === Write to CSV ===
output_file = "output.csv"
with open(output_file, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print(f"✅ Conversion complete! CSV saved as: {output_file}")
