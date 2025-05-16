
import streamlit as st
import subprocess
import os
import glob
import shutil
from datetime import datetime

# ==== Streamlit UI ====
st.title("🔧 Secure Script Runner")

# Step 1: Script selection
scripts = {
    "Apollo Lead Gen Automation": "apollo_lead_gen_automation.py",
    "Final Filteration & Mapping": "final_filteration_mapping.py",
    "JSON to CSV Converter": "json_to_csv_convertor.py",
    "LLM Calling Script": "LLM_calling_script.py",
    "LLM Title Classifier": "LLM_title_classifier.py"
}

selected_script = st.selectbox("Select a script to run:", list(scripts.keys()))

# Step 2: User input fields
st.subheader("Provide Required Inputs")
api_key = st.text_input("🔐 API Key (if required by script)", type="password")
uploaded_files = st.file_uploader("📤 Upload files (if needed by script)", accept_multiple_files=True)

# Step 3: Execution trigger
if st.button("🚀 Run Script"):
    working_dir = "/tmp/script_runner"
    os.makedirs(working_dir, exist_ok=True)

    # Save uploaded files
    for file in uploaded_files:
        file_path = os.path.join(working_dir, file.name)
        with open(file_path, "wb") as f:
            f.write(file.getvalue())

    # Set environment variable for API key
    if api_key:
        os.environ["API_KEY"] = api_key

    # Step 4: Run selected script using subprocess
    st.info(f"⏳ Running `{scripts[selected_script]}`...")
    with st.spinner("Processing..."):
        result = subprocess.run(
            ["python3", f"/mount/src/{scripts[selected_script]}"],
            cwd=working_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

    st.subheader("📜 Logs")
    st.code(result.stdout)

    # Step 5: Show output files
    st.subheader("📁 Output Files")
    output_files = glob.glob(os.path.join(working_dir, "*"))
    for f in output_files:
        if f.endswith(".json") or f.endswith(".csv"):
            with open(f, "rb") as data:
                st.download_button(f"⬇️ Download {os.path.basename(f)}", data, file_name=os.path.basename(f))
