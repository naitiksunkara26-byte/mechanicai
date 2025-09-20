# streamlit_app.py
import streamlit as st
import tempfile
from pathlib import Path
from ultralytics import YOLO
import cv2
import openai

# -------------------------------
# CONFIG
# -------------------------------
st.set_page_config(page_title="Car Repair AI", layout="wide")
openai.api_key = st.secrets.get("OPENAI_API_KEY")  # Set this in Streamlit secrets

# -------------------------------
# FUNCTIONS
# -------------------------------
def analyze_video(file_path):
    detected = set()
    model = YOLO("yolov8n.pt")  # Add yolov8n.pt to your repo
    cap = cv2.VideoCapture(file_path)

    tmp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(tmp_output.name, fourcc, fps, (width, height))

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame)
        frame = results[0].plot()
        out.write(frame)
        detected.update([x['name'] for x in results[0].pandas().xyxy[0].to_dict(orient='records')])

    cap.release()
    out.release()
    return list(detected), tmp_output.name

def get_ai_solution(description):
    try:
        prompt = f"Provide a detailed step-by-step solution for this car problem: {description}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role":"user", "content":prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"AI solution could not be fetched: {e}"

# -------------------------------
# APP LAYOUT
# -------------------------------
st.title("🔧 Car Repair AI")

# Sidebar vehicle info
with st.sidebar:
    st.header("Vehicle Information")
    vehicle_make = st.text_input("Vehicle Make", "Toyota")
    vehicle_model = st.text_input("Vehicle Model", "Camry")
    vehicle_year = st.text_input("Vehicle Year", "2015")

# Chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# User input
description = st.text_input("Describe the issue with your car:")
uploaded_file = st.file_uploader(
    "Upload a car audio or video file (MP3, WAV, M4A, MP4, MOV)",
    type=["mp3", "wav", "m4a", "mp4", "mov"]
)

if st.button("Diagnose"):
    visual_issues = []
    processed_video = None

    # Analyze video if uploaded
    if uploaded_file:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix)
        tmp.write(uploaded_file.read())
        tmp.flush()
        if Path(uploaded_file.name).suffix.lower() in [".mp4", ".mov"]:
            visual_issues, processed_video = analyze_video(tmp.name)

    # AI solution
    solution = get_ai_solution(description)

    # DIY vs Mechanic options
    diy_cost = "$50 (parts & tools)"
    mechanic_cost = "$120 (labor + estimate)"
    options_text = f"""
**Options:**
- DIY: {diy_cost}
- Take to Mechanic: {mechanic_cost}
"""

    # Add to chat history
    st.session_state.chat_history.append({
        "description": description,
        "visual_issues": visual_issues,
        "solution": solution,
        "options": options_text,
        "processed_video": processed_video
    })

# Display chat history
for i, entry in enumerate(st.session_state.chat_history):
    st.markdown(f"### Issue {i+1}: {entry['description']}")
    if entry['visual_issues']:
        st.markdown(f"**Detected Visual Issues:** {', '.join(entry['visual_issues'])}")
    st.markdown(f"**AI Suggested Solution:** {entry['solution']}")
    st.markdown(entry['options'])
    if entry['processed_video']:
        st.video(entry['processed_video'])
    st.markdown("---")

