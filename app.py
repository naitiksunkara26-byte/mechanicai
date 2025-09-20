# app.py
import os
import tempfile
from pathlib import Path
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
import requests
import openai  # For AI search
import cv2
from ultralytics import YOLO

app = FastAPI(title="Car Repair AI Web API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set OpenAI API key for searches
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
openai.api_key = OPENAI_API_KEY

def analyze_video(file_path):
    detected = set()
    model = YOLO("yolov8n.pt")  # YOLO model
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

def search_solution_online(description):
    prompt = f"Suggest detailed step-by-step solutions for this car issue: {description}"
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"Could not fetch online solution: {e}"

@app.post("/api/diagnose_ai")
async def diagnose_ai(
    description: str = Form(...),
    vehicle_make: str = Form(None),
    vehicle_model: str = Form(None),
    vehicle_year: str = Form(None),
    file: UploadFile | None = None
):
    vehicle_make = vehicle_make or "Toyota"
    vehicle_model = vehicle_model or "Camry"
    vehicle_year = vehicle_year or "2015"

    visual_issues = []
    processed_video = None

    if file:
        suffix = Path(file.filename).suffix or ".mp4"
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(await file.read())
        tmp.flush()

        if suffix.lower() in [".mp4", ".mov", ".m4a"]:
            visual_issues, processed_video = analyze_video(tmp.name)
        tmp.close()

    online_solution = search_solution_online(description)

    diy_cost = 50  # Estimated parts/tools
    mechanic_cost = 120  # Estimated mechanic

    return {
        "ok": True,
        "diagnosis": {
            "description": description,
            "visual_issues": visual_issues,
            "processed_video_path": processed_video,
            "online_solution": online_solution,
            "options": {
                "DIY": f"${diy_cost} estimated",
                "Mechanic": f"${mechanic_cost} estimated"
            }
        }
    }
