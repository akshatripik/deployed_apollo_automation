import requests
import json

# === 1. Setup ===
API_KEY = input("🔐 Enter your Apollo API Key: ").strip()
HEADERS = {
    "Content-Type": "application/json",
    "Cache-Control": "no-cache",
    "X-Api-Key": API_KEY
}

# === 2. Input Person ID ===
person_id = input("🆔 Enter Apollo Person ID: ").strip()

def enrich_person(purchase_contact=True):
    payload = {
        "person_id": person_id,
        "purchase_contact": purchase_contact
    }
    response = requests.post(
        "https://api.apollo.io/v1/people/enrich",
        headers=HEADERS,
        data=json.dumps(payload)
    )
    if response.status_code != 200:
        print(f"❌ API error: {response.status_code} - {response.text}")
        return None
    return response.json().get("person", {})

# === 3. Enrich with purchase_contact=True and save/show output ===
person = enrich_person(purchase_contact=True)

if not person:
    print("⚠️ No person found or invalid ID.")
    exit()

# Save to JSON file
with open("F_EnrichOutput.json", "w", encoding="utf-8") as f:
    json.dump(person, f, ensure_ascii=False, indent=2)

# # Show JSON output in runtime
# print("\n=== Enriched Person JSON Output ===")
# print(json.dumps(person, ensure_ascii=False, indent=2))

# Show selected fields in runtime
print("\n=== Selected Enriched Fields ===")
print(f"Name   : {person.get('first_name', '')} {person.get('last_name', '')}")
print(f"ID     : {person.get('id', '')}")
print(f"Title  : {person.get('title', '')}")
print(f"Company: {person.get('organization', {}).get('name', '')}")
print(f"Email  : {person.get('email', '')}")

# Print person's phone numbers (not organization phones)
phones = person.get('phone_numbers', [])
if phones:
    print(f"Phone  : {', '.join(phones)}")
else:
    print("Phone  : Not available")

# === All other steps commented out ===
# email = person.get("email", "")
# phones = person.get("phone_numbers", [])
# email_locked = not email or "not_unlocked" in email
# phone_locked = not phones
# wants_email = False
# wants_phone = False
# if email_locked:
#     wants_email = input("❓ Email not available. Enrich to unlock? (y/n): ").strip().lower() == 'y'
# else:
#     print(f"📧 Email: {email}")
# if phone_locked:
#     wants_phone = input("❓ Mobile not available. Enrich to unlock? (y/n): ").strip().lower() == 'y'
# else:
#     print(f"📱 Phone(s): {', '.join(phones)}")
# if wants_email or wants_phone:
#     person = enrich_person(purchase_contact=True)
#     print("\n🔁 Re-enriched with contact unlock...")
#     email = person.get("email", "")
#     phones = person.get("phone_numbers", [])
#     if wants_email:
#         print(f"📧 Email: {email if email else 'Still not available'}")
#     if wants_phone:
#         print(f"📱 Phone(s): {', '.join(phones) if phones else 'Still not available'}")
# print("\n✅ Enrichment complete.")
