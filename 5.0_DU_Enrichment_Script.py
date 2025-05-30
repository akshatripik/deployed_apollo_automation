import os
import json
import requests

# === API CONFIGURATION ===
API_KEY = input("🔐 Enter your Apollo API Key: ").strip()
HEADERS = {
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "Api-Key": API_KEY,
}

# === FUNCTION: ENRICH PERSON ===
def enrich_person(person_id):
    url = "https://api.apollo.io/v1/people/enrich"
    data = {"id": person_id}
    response = requests.post(url, headers=HEADERS, json=data)
    if response.status_code == 200:
        return response.json().get("person", {})
    else:
        print(f"❌ Failed to enrich person with ID {person_id}: {response.text}")
        return {}

# === SINGLE ENTRY FLOW ===
def single_enrichment():
    person_id = input("🔑 Enter Apollo Person ID: ").strip()
    print(f"🔍 Enriching data for Person ID: {person_id}")
    person = enrich_person(person_id)
    print(json.dumps(person, indent=2))

# === BULK ENRICHMENT FLOW WITH TERMINAL FILE SELECTION ===
def bulk_enrichment():
    json_files = [f for f in os.listdir('.') if f.endswith('.json')]

    if not json_files:
        print("❌ No JSON files found in the current directory.")
        return

    print("\n📂 Available JSON files:")
    for idx, filename in enumerate(json_files):
        print(f"{idx + 1}. {filename}")

    choice = input("\nEnter the number of the file to use: ").strip()
    try:
        choice_idx = int(choice) - 1
        file_path = json_files[choice_idx]
    except (IndexError, ValueError):
        print("❌ Invalid selection.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        people = json.load(f)

    enriched_people = []
    for entry in people:
        person_id = entry.get("id")
        if not person_id:
            print(f"⚠️ Missing ID in entry: {entry}")
            continue
        print(f"🔍 Enriching ID: {person_id} ({entry.get('first_name', '')} {entry.get('last_name', '')})")
        enriched = enrich_person(person_id)
        enriched_people.append(enriched)

    output_path = os.path.splitext(file_path)[0] + "_enriched.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(enriched_people, f, indent=2)

    print(f"✅ Enrichment complete. Saved to: {output_path}")

# === MAIN FLOW ===
def main():
    print("\n📌 Choose Enrichment Mode:")
    print("1. Single Entry Enrichment")
    print("2. Bulk Enrichment from JSON file")

    choice = input("Enter 1 or 2: ").strip()

    if choice == "1":
        single_enrichment()
    elif choice == "2":
        bulk_enrichment()
    else:
        print("❌ Invalid choice. Exiting.")

if __name__ == "__main__":
    main()
