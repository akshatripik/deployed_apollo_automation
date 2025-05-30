import requests
import json

# === 1. API Key and Setup ===
API_KEY = input("🔐 Enter your Apollo API Key: ").strip()
HEADERS = {
    "Cache-Control": "no-cache",
    "Content-Type": "application/json",
    "X-Api-Key": API_KEY
}

# === 2. Input: Country and Company Name ===
country = input("🌍 Enter Country (e.g., USA): ").strip()
company_name = input("🏢 Enter Company Name (e.g., Cemex): ").strip()

# === 3. Search for Matching Organizations ===
print(f"\n📡 API HIT #1: Searching for organizations matching '{company_name}'")
org_search_url = "https://api.apollo.io/v1/organizations/search"
org_payload = {
    "q_organization_name": company_name,
    "page": 1,
    "per_page": 10
}

org_response = requests.post(org_search_url, headers=HEADERS, data=json.dumps(org_payload))
api_hit_count = 1

orgs = org_response.json().get("organizations", [])
if not orgs:
    print("⚠️ No organizations found.")
    exit()

print(f"\n✅ Found {len(orgs)} matching organizations:\n")
for idx, org in enumerate(orgs):
    print(f"{idx:02d}. 🏢 {org.get('name')} | 🌐 {org.get('website_url')} | 🌍 {org.get('location_country')}")
    print(f"     🔑 ID: {org.get('id')}\n")

# # === 4. Org Selection ===
# selected_idx = input("🔢 Enter org index (leave blank for all): ").strip()
# if selected_idx == "":
#     selected_org_ids = [org.get("id") for org in orgs]
#     org_label = f"ALL matched '{company_name}' orgs"
# else:
#     selected_org_ids = [orgs[int(selected_idx)].get("id")]
#     org_label = orgs[int(selected_idx)].get("name")

selected_idx = input("🔢 Enter org index (comma-separated for multiple, leave blank for all): ").strip()

if selected_idx == "":
    selected_org_ids = [org.get("id") for org in orgs]
    org_label = f"ALL matched '{company_name}' orgs"
else:
    try:
        indices = [int(i.strip()) for i in selected_idx.split(",") if i.strip().isdigit()]
        selected_org_ids = [orgs[i].get("id") for i in indices]
        org_label = ", ".join([orgs[i].get("name") for i in indices])
    except Exception as e:
        print(f"❌ Invalid input. Please enter valid index numbers. Error: {e}")
        exit()

# === 5. Choose API Call Depth ===
only_one_page = input("📄 Fetch ONLY ONE PAGE per org? (y/n): ").strip().lower() == 'y'

# === 6. People Search ===
people_url = "https://api.apollo.io/v1/mixed_people/search"
all_people = []

for org_id in selected_org_ids:
    org_info = next((o for o in orgs if o.get("id") == org_id), {})
    org_name = org_info.get("name", "Unknown Org")

    page = 1
    per_page = 100

    while True:
        print(f"📡 API HIT #{api_hit_count + 1}: Fetching page {page} for org '{org_name}'...")
        people_payload = {
            "organization_ids": [org_id],
            "person_locations": [country],
            "per_page": per_page,
            "page": page
        }

        response = requests.post(people_url, headers=HEADERS, data=json.dumps(people_payload))
        api_hit_count += 1

        data = response.json()
        people = data.get("people", [])
        pagination = data.get("pagination", {})
        total_entries = pagination.get("total_entries", 0)

        if not people:
            break

        # Append full raw person data
        all_people.extend(people)

        if only_one_page or page * per_page >= total_entries:
            break
        page += 1

    print(f"🔍 Org: {org_name} | ID: {org_id} | Found: {len(people)} people on page {page}")

# === 7. Save Results and Final API Hit Count ===
print(f"\n👥 Total people fetched: {len(all_people)}")
print(f"📊 Total API hits made (including org search): {api_hit_count}")
with open("A_full_people_data.json", "w", encoding="utf-8") as f:
    json.dump(all_people, f, indent=2, ensure_ascii=False)
print("💾 Data saved to 'A_full_people_data.json'")

# === 8. Extract Only 'id' and 'title' from Saved Data ===
filtered_filename = "B_people_id_title.json"

with open("A_full_people_data.json", "r", encoding="utf-8") as f:
    raw_people = json.load(f)

filtered_people = [{"id": p.get("id"), "title": p.get("title")} for p in raw_people]

with open(filtered_filename, "w", encoding="utf-8") as f:
    json.dump(filtered_people, f, indent=2, ensure_ascii=False)

print(f"✅ Filtered file with 'id' and 'title' saved as '{filtered_filename}'")

