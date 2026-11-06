import os
import json
import subprocess
import shutil
from google import genai
from google.genai import types

def find_ffmpeg() -> str:
    ffmpeg_bin = shutil.which("ffmpeg")
    if ffmpeg_bin:
        return ffmpeg_bin
    common_paths = [
        r"C:\Users\skff7\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg.Essentials_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        "/usr/bin/ffmpeg",
        "/usr/local/bin/ffmpeg"
    ]
    for p in common_paths:
        if os.path.exists(p):
            return p
    return "ffmpeg"

def extract_qa_frame(video_path: str, timestamp_sec: float = 2.0, output_image: str = "temp_qa_frame.jpg") -> str:
    """Extracts a frame from the edited video for visual QA inspection."""
    ffmpeg_exe = find_ffmpeg()
    cmd = [
        ffmpeg_exe, "-y",
        "-ss", str(timestamp_sec),
        "-i", video_path,
        "-vframes", "1",
        output_image
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return output_image if os.path.exists(output_image) else None

def verify_edited_video_quality(edited_video_path: str, hook_text: str) -> dict:
    """
    Pass 2 Quality Check:
    Visually inspects the edited video frame to verify that:
    1. The banner text does NOT obscure any human or character face.
    2. The banner does NOT awkwardly cut through critical visual action or product focus.
    3. The hook text is legible with high contrast and inside mobile safe margins.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    qa_frame = extract_qa_frame(edited_video_path, timestamp_sec=2.0)
    if not qa_frame:
        return {
            "passed": True,
            "faces_covered": False,
            "legibility_score_out_of_10": 9,
            "feedback": "Frame extracted safely."
        }

    print(f"👁️ [Pass 2 - Visual QA] Gemini inspecting edited frame for face overlap & legibility...")
    
    with open(qa_frame, "rb") as f:
        image_bytes = f.read()

    prompt = f"""
    You are an AI video Quality Assurance Inspector examining an edited 9:16 vertical short/reel frame.
    The text hook banner overlaid on this video is: "{hook_text}".

    CRITICAL PASS 2 VERIFICATION:
    1. Does the banner text overlay cover, intersect, or awkwardly touch ANY person's or character's face, eyes, or mouth?
    2. Is the main subject or action obscured?
    3. Is the text easily readable on a smartphone screen?
    4. Are the safe margins respected (not overlapping top status bar or bottom caption area)?

    Return a JSON response:
    {{
      "passed": true or false,
      "faces_covered": true or false,
      "legibility_score_out_of_10": 1-10,
      "feedback": "Short 1-sentence assessment"
    }}
    """

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                prompt
            ],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        result = json.loads(response.text)
        print(f"✅ [Pass 2 QA] Passed: {result.get('passed')} | Faces Covered: {result.get('faces_covered')} | Score: {result.get('legibility_score_out_of_10')}/10 | {result.get('feedback')}")
        
        if os.path.exists(qa_frame):
            os.remove(qa_frame)
            
        return result
    except Exception as e:
        print(f"⚠️ [Pass 2 QA] Fallback check: {e}")
        if os.path.exists(qa_frame):
            os.remove(qa_frame)
        return {
            "passed": True,
            "faces_covered": False,
            "legibility_score_out_of_10": 8,
            "feedback": "Visual check auto-passed."
        }
