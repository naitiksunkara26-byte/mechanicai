# streamlit_app.py
import streamlit as st
import requests

st.set_page_config(page_title="Car Repair AI", layout="wide")
st.title("🔧 Car Repair AI")

# Session state for chat
if "history" not in st.session_state:
    st.session_state.history = []

description = st.text_input("Describe the issue with your car:")
vehicle_make = st.text_input("Vehicle Make", "Toyota")
vehicle_model = st.text_input("Vehicle Model", "Camry")
vehicle_year = st.text_input("Vehicle Year", "2015")
uploaded_file = st.file_uploader("Upload a car audio or video file", type=["mp3","wav","m4a","mp4","mov"])

if st.button("Diagnose"):
    files = {"file": uploaded_file} if uploaded_file else None
    data = {
        "description": description,
        "vehicle_make": vehicle_make,
        "vehicle_model": vehicle_model,
        "vehicle_year": vehicle_year
    }
    try:
        response = requests.post("http://localhost:8000/api/diagnose_ai", data=data, files=files)
        result = response.json()
        st.session_state.history.append(result["diagnosis"])
    except Exception as e:
        st.error(f"Error contacting backend: {e}")

# Display history
for entry in st.session_state.history:
    st.markdown("### 🔍 Diagnosis")
    st.write(entry["description"])
    if entry.get("visual_issues"):
        st.write("**Detected Visual Issues:**", entry["visual_issues"])
    if entry.get("online_solution"):
        st.markdown("**Suggested Solution:**")
        st.write(entry["online_solution"])
    if entry.get("processed_video_path"):
        st.video(entry["processed_video_path"])
    st.markdown("**Options:**")
    for k,v in entry["options"].items():
        st.write(f"{k}: {v}")
    st.markdown("---")
