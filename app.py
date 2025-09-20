# streamlit_app.py
import streamlit as st
import tempfile
from pathlib import Path
import os
import cv2
from ultralytics import YOLO

# Dummy AI analysis functions
def analyze_audio(file_path):
    return ["engine knock detected"]

def analyze_video(file_path):
    visual_objects_detected = set()
    model = YOLO("yolov8n.pt")  # Ensure this file is in the repo or change path

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
        detected_names = [x['name'] for x in results[0].pandas().xyxy[0].to_dict(orient='records')]
        visual_objects_detected.update(detected_names)

    cap.release()
    out.release()
    return list(visual_objects_detected), tmp_output.name

def map_to_causes(audio_tags, description):
    parts = ["spark plug", "headlight"]
    probable_causes = [f"Probable issue based on audio: {tag}" for tag in audio_tags]
    if description:
        probable_causes.append(f"User description: {description}")
    return probable_causes, parts

def parts_lookup(part, make, model, year):
    return {"results":[{"name":part, "link":f"https://www.ebay.com/sch/i.html?_nkw={part}+{make}+{model}+{year}"}]}

st.title("Car Repair AI")

description = st.text_input("Describe the problem")
vehicle_make = st.text_input("Vehicle Make", "Toyota")
vehicle_model = st.text_input("Vehicle Model", "Camry")
vehicle_year = st.text_input("Vehicle Year", "2015")
uploaded_file = st.file_uploader("Upload audio/video file")

if st.button("Diagnose"):
    audio_tags, visual_issues, processed_video = [], [], None

    if uploaded_file:
        suffix = Path(uploaded_file.name).suffix or ".mp4"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded_file.read())
        tmp.flush()

        if suffix.lower() in [".wav", ".mp3", ".m4a"]:
            audio_tags = analyze_audio(tmp.name)
        else:
            visual_issues, processed_video = analyze_video(tmp.name)
            audio_tags = analyze_audio(tmp.name)
        tmp.close()

    probable_causes, parts = map_to_causes(audio_tags, description)
    for vi in visual_issues:
        probable_causes.append(f"Detected visual issue: {vi}")
    probable_causes = list(set(probable_causes))

    parts_with_links = []
    for part in parts:
        parts_with_links.append({part: parts_lookup(part, vehicle_make, vehicle_model, vehicle_year)["results"]})

    steps = [f"Check {cause.lower()} carefully." for cause in probable_causes]
    mechanics = [{"name":"Joe's Auto Repair","location":"123 Main St","price_estimate":"$120"}]

    st.subheader("Diagnosis Results")
    st.write("Probable Causes:", probable_causes)
    st.write("Steps:", steps)
    st.write("Parts:", parts)
    st.write("Parts with Links:", parts_with_links)
    st.write("Mechanics:", mechanics)
    st.write("Audio Tags:", audio_tags)
    st.write("Visual Issues:", visual_issues)

    if processed_video:
        st.video(processed_video)
