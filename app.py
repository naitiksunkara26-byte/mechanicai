# app.py
import os
import tempfile
from pathlib import Path
import streamlit as st
import requests
import cv2
from ultralytics import YOLO

# ---------------------------
# Config
# ---------------------------
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.environ.get("GOOGLE_CSE_ID")
DEFAULT_VEHICLE = {"make": "Toyota", "model": "Camry", "year": "2015"}

# ---------------------------
# Helper Functions
# ---------------------------

def analyze_audio(file_path):
    """Dummy placeholder for audio analysis"""
    return ["engine knock detected"]

def analyze_video(file_path):
    """Analyze video using YOLO and return detected objects"""
    visual_objects_detected = set()
    tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    
    try:
        model = YOLO("yolov8n.pt")  # Make sure you have this model in the working dir
    except Exception:
        return ["Unable to load YOLO model"], None

    cap = cv2.VideoCapture(file_path)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(tmp_output.name, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        frame = results[0].plot()
        out.write(frame)
        detected = [x['name'] for x in results[0].pandas().xyxy[0].to_dict(orient='records')]
        visual_objects_detected.update(detected)

    cap.release()
    out.release()
    return list(visual_objects_detected), tmp_output.name

def map_to_causes(audio_tags, description):
    """Map audio/video tags + description to probable causes"""
    parts = ["spark plug", "headlight", "tire"]
    probable_causes = [f"Probable issue based on audio/video: {tag}" for tag in audio_tags]
    if description:
        probable_causes.append(f"User description: {description}")
    return probable_causes, parts

def parts_lookup(part, make, model, year):
    """Generate parts search link"""
    return {"results":[{"name":part, "link":f"https://www.ebay.com/sch/i.html?_nkw={part}+{make}+{model}+{year}"}]}

def search_internet_for_solution(query, num_results=3):
    """Search Google Custom Search API for DIY solutions"""
    if not GOOGLE_API_KEY or not GOOGLE_CSE_ID:
        return [{"title": f"DIY fix for {query}", "url": "https://www.google.com", "price_estimate":"$50"}]

    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }
    try:
        resp = requests.get(url, params=params).json()
        results = []
        for item in resp.get("items", []):
            results.append({
                "title": item.get("title"),
                "url": item.get("link"),
                "price_estimate": "DIY estimate varies"
            })
        return results
    except Exception:
        return [{"title": f"DIY fix for {query}", "url": "https://www.google.com", "price_estimate":"$50"}]

# ---------------------------
# Streamlit UI
# ---------------------------

st.set_page_config(page_title="Car Repair AI", layout="wide")
st.title("🔧 Car Repair AI")

# --- Input Section ---
with st.form("diagnose_form"):
    description = st.text_input("Describe the issue with your car")
    vehicle_make = st.text_input("Vehicle Make", DEFAULT_VEHICLE["make"])
    vehicle_model = st.text_input("Vehicle Model", DEFAULT_VEHICLE["model"])
    vehicle_year = st.text_input("Vehicle Year", DEFAULT_VEHICLE["year"])
    file = st.file_uploader("Upload a car audio or video file", type=["mp3","wav","m4a","mp4","mpeg4"])
    submitted = st.form_submit_button("Diagnose")

# --- Diagnosis ---
if submitted:
    audio_tags, visual_issues, processed_video = [], [], None

    if file:
        suffix = Path(file.name).suffix or ".mp4"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(file.read())
        tmp.flush()

        if suffix.lower() in [".wav", ".mp3", ".m4a"]:
            audio_tags = analyze_audio(tmp.name)
        else:
            visual_issues, processed_video = analyze_video(tmp.name)
            audio_tags = analyze_audio(tmp.name)
        tmp.close()

    probable_causes, parts = map_to_causes(audio_tags + visual_issues, description)

    # --- Display Diagnosis ---
    st.subheader("🔍 Probable Causes")
    for cause in probable_causes:
        st.write(f"- {cause}")

    # --- Parts ---
    st.subheader("🛠️ Recommended Parts")
    for part in parts:
        link = parts_lookup(part, vehicle_make, vehicle_model, vehicle_year)["results"][0]["link"]
        st.markdown(f"- [{part}]({link})")

    # --- Video Preview ---
    if processed_video:
        st.subheader("🎥 Processed Video")
        st.video(processed_video)

    # --- DIY vs Mechanic Options ---
    st.subheader("💡 Repair Options")

    st.markdown("### 🏠 DIY Solutions")
    for cause in probable_causes:
        diy_options = search_internet_for_solution(f"{vehicle_year} {vehicle_make} {vehicle_model} {cause}")
        for opt in diy_options:
            st.markdown(f"- [{opt['title']}]({opt['url']}) – {opt['price_estimate']}")

    st.markdown("### 👨‍🔧 Mechanic Options")
    mechanics = [{"name":"Joe's Auto Repair","location":"123 Main St","price_estimate":"$120"}]
    for mech in mechanics:
        st.write(f"- {mech['name']} – {mech['location']} – {mech['price_estimate']}")

    # --- Chat / Notes ---
    st.subheader("💬 Notes / Chat History")
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    user_note = st.text_area("Add your notes or questions below and hit Enter")
    if user_note:
        st.session_state.chat_history.append(user_note)
    for note in st.session_state.chat_history:
        st.write(f"- {note}")
