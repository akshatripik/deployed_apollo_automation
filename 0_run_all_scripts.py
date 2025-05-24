import os
import subprocess
import sys

# === Identify Current Script ===
current_script = os.path.basename(__file__)

# === List All Python Scripts Except This One ===
all_scripts = sorted([
    f for f in os.listdir() 
    if f.endswith(".py") and f != current_script
])

# === Display Scripts ===
print("\n📜 Available Scripts:")
for idx, script in enumerate(all_scripts):
    print(f"{idx}: {script}")

# === Select Starting Script ===
while True:
    try:
        start_index = int(input("\n🚀 Enter the index of the script you want to start running from: "))
        if 0 <= start_index < len(all_scripts):
            break
        else:
            print("❌ Invalid index. Try again.")
    except ValueError:
        print("❌ Please enter a number.")

# === Run Scripts in Order from Selected Index ===
for i in range(start_index, len(all_scripts)):
    script_to_run = all_scripts[i]
    print(f"\n▶️ Running: {script_to_run}")
    subprocess.run([sys.executable, script_to_run])

    if i < len(all_scripts) - 1:
        cont = input("⏭️ Do you want to run the next script? (y/n): ").strip().lower()
        if cont != 'y':
            print("🛑 Stopping execution.")
            break
    else:
        print("✅ All scripts completed.")
