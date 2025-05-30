import json
import csv
import os

# === List and Choose JSON File from Directory ===
def choose_file_from_dir(prompt_text):
    files = [f for f in os.listdir() if f.endswith('.json')]
    files.sort()
    if not files:
        raise Exception("❌ No JSON files found in the current directory.")

    print(f"\n📂 Available JSON files for {prompt_text}:")
    for idx, file in enumerate(files):
        print(f"  [{idx}] {file}")

    while True:
        try:
            choice = int(input(f"\n✏️ Enter the index of the {prompt_text} file: ").strip())
            if 0 <= choice < len(files):
                print(f"✅ Selected file: {files[choice]}")
                return files[choice]
            else:
                print("⚠️ Invalid index. Try again.")
        except ValueError:
            print("⚠️ Please enter a valid number.")

# === Load JSON ===
def load_json(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

# === Save JSON ===
def save_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# === Save CSV ===
def save_csv(data, filename):
    fieldnames = ["id", "first_name", "last_name", "linkedin_url", "organization_name", "title", "translated_title"]
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in fieldnames})

# === Main Workflow ===
def main():
    # Step 1: Load Classification File
    classification_file = choose_file_from_dir("Classification")
    classification_data = load_json(classification_file)

    # Step 2: Build map of RELEVANT entries
    relevant_map = {
        entry["id"]: {
            "title": entry.get("title", ""),
            "translated_title": entry.get("translated_title", "")
        }
        for entry in classification_data if entry.get("classification") == "RELEVANT"
    }

    # Step 3: Load People Data File
    people_file = choose_file_from_dir("People")
    people_data = load_json(people_file)

    # Step 4: Filter and enrich with classification titles
    final_data = []
    for person in people_data:
        person_id = person.get("id")
        if person_id in relevant_map:
            org_name = ""
            if isinstance(person.get("employment_history"), list) and person["employment_history"]:
                org_name = person["employment_history"][0].get("organization_name", "")
            final_data.append({
                "id": person_id,
                "first_name": person.get("first_name", ""),
                "last_name": person.get("last_name", ""),
                "linkedin_url": person.get("linkedin_url", ""),
                "organization_name": org_name,
                "title": relevant_map[person_id].get("title", ""),
                "translated_title": relevant_map[person_id].get("translated_title", "")
            })

    # Step 5: Save Outputs
    save_json(final_data, "D_filtered_relevant_entries.json")
    save_csv(final_data, "E_filtered_relevent_entries.csv")
    print("\n🎉 Files saved as 'D_filtered_relevant_entries.json' and 'E_filtered_relevent_entries.csv'")

if __name__ == "__main__":
    main()
