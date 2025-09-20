import os
import requests
import streamlit as st

# Hugging Face + Replicate API keys (set these in Streamlit Cloud secrets)
HF_TOKEN = os.environ.get("HF_TOKEN")
REPLICATE_TOKEN = os.environ.get("REPLICATE_TOKEN")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")

st.title("🔧 Car Repair AI")

description = st.text_area("Describe the issue with your car:")
make = st.text_input("Vehicle Make", "Toyota")
model = st.text_input("Vehicle Model", "Camry")
year = st.text_input("Vehicle Year", "2015")
uploaded_file = st.file_uploader("Upload a car audio or video file", type=["mp3", "wav", "m4a", "mp4"])

if st.button("Diagnose"):
    probable_causes = []
    audio_tags, visual_issues = [], []

    # 1️⃣ Audio analysis with Hugging Face
    if uploaded_file and uploaded_file.type.startswith("audio/"):
        st.info("Analyzing audio...")
        audio_bytes = uploaded_file.read()
        headers = {"Authorization": f"Bearer {HF_TOKEN}"}
        resp = requests.post(
            "https://api-inference.huggingface.co/models/facebook/wav2vec2-base-960h",
            headers=headers,
            data=audio_bytes
        )
        if resp.status_code == 200:
            text = resp.json().get("text", "")
            if "knock" in text.lower():
                audio_tags.append("engine knock detected")
            if "squeak" in text.lower():
                audio_tags.append("brake squeak detected")

    # 2️⃣ Video analysis with Replicate YOLO
    if uploaded_file and uploaded_file.type.startswith("video/"):
        st.info("Analyzing video with YOLOv8...")
        resp = requests.post(
            "https://api.replicate.com/v1/predictions",
            headers={"Authorization": f"Token {REPLICATE_TOKEN}"},
            json={
                "version": "yolov8",  # Replicate’s YOLOv8 model slug
                "input": {"video": uploaded_file}
            }
        )
        if resp.ok:
            data = resp.json()
            visual_issues = data.get("output", [])
    
    # 3️⃣ Map to causes
    if audio_tags:
        probable_causes.extend([f"Probable issue from audio: {tag}" for tag in audio_tags])
    if visual_issues:
        probable_causes.extend([f"Detected visual issue: {vi}" for vi in visual_issues])
    if description:
        probable_causes.append(f"User description: {description}")

    # 4️⃣ Show causes
    st.subheader("🔍 Probable Causes")
    for cause in probable_causes:
        st.write(f"- {cause}")

    # 5️⃣ Parts with links
    st.subheader("🛠️ Recommended Parts")
    parts = ["spark plug", "headlight"]
    for part in parts:
        link = f"https://www.ebay.com/sch/i.html?_nkw={part}+{make}+{model}+{year}"
        st.markdown(f"- [{part}]({link})")

    # 6️⃣ YouTube Fix Videos
    st.subheader("📺 How-To Fix Videos")
    if YOUTUBE_API_KEY and probable_causes:
        query = f"How to fix {year} {make} {model} {probable_causes[0]}"
        yt_resp = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={"part":"snippet","q":query,"type":"video","maxResults":3,"key":YOUTUBE_API_KEY}
        )
        for it in yt_resp.json().get("items", []):
            vid = it["id"]["videoId"]
            title = it["snippet"]["title"]
            st.markdown(f"[{title}](https://www.youtube.com/watch?v={vid})")

    # 7️⃣ Mechanic suggestion
    st.subheader("👨‍🔧 Nearby Mechanic Suggestion")
    st.write("Joe's Auto Repair – 123 Main St – $120 estimate")
