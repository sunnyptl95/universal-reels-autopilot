import os
import json
import time
from google import genai
from google.genai import types

def analyze_video_and_generate_hooks(video_path: str, memory_context: dict = None) -> dict:
    """
    Universal Zero-Prompt Multimodal Reel Analyzer:
    Auto-detects ANY video genre (Gym/Fitness, Comedy/Memes, AI/Tech, Finance, Motivation,
    Podcasts, Anime, Lifestyle), determines the emotional core or punchline, detects safe-zones
    to protect faces, and generates viral hook, caption, and niche-specific trending hashtags.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing!")

    client = genai.Client(api_key=api_key)
    
    print(f"🧠 [Pass 1 - Universal AI Vision] Ingesting video: {os.path.basename(video_path)}...")
    video_file = client.files.upload(file=video_path)
    
    # Wait for processing
    while video_file.state.name == "PROCESSING":
        print("⏳ [AI Vision] Video decoding in progress, waiting 3s...")
        time.sleep(3)
        video_file = client.files.get(name=video_file.name)
        
    if video_file.state.name == "FAILED":
        raise RuntimeError("Gemini failed to process the video.")

    learnings_summary = ""
    if memory_context and "learnings" in memory_context:
        learnings_summary = "Past Performance Learnings & Anti-Flop Rules to follow:\n" + "\n".join(
            f"- {l}" for l in memory_context.get("learnings", [])[-3:]
        )

    system_prompt = f"""
    You are an elite, multi-niche viral Instagram Reels strategist and visual editor.
    Carefully inspect and listen to the uploaded 9:16 short video.

    STEP 1: AUTO-DETECT NICHE & MOOD
    - Detect the niche (e.g. Gym/Fitness, Motivation/Stoic, AI/Tech, Comedy/Memes, Anime/Animation, Business/Finance, Podcast clip).
    - Identify the key visual subject, voiceover/dialogues, emotional climax, or comedic punchline.

    STEP 2: SAFE-ZONE VISUAL POSITIONING
    - Where are the subject's face, eyes, or primary visual focus located?
    - Determine safe Y-coordinate (default is y=250 in 1080x1920) so the banner text NEVER cuts through faces or critical screen elements.

    STEP 3: HOOK, CAPTION & VIRAL HASHTAGS
    - Hook: Short, punchy (5-8 words max) on-screen text banner that forces the user to pause and watch.
      - If Gym/Motivation: High energy, stoic, discipline-focused.
      - If Comedy/Memes: Relatable friend roast, sarcasm, situational humor.
      - If Tech/AI: Curiosity gap, futuristic insight.
      - If General: Catchy emotional trigger.
    - Caption: 2-3 engaging lines tailored to the niche with an active Call To Action (tag friends, drop a comment, save for later).
    - Hashtags: 12-15 trending, high-volume hashtags specifically matching this detected niche.

    {learnings_summary}

    Respond ONLY in strict JSON:
    {{
      "detected_niche": "e.g. Fitness / Comedy / AI / Motivation",
      "video_summary": "1-sentence summary",
      "hook_text": "5-8 word high-impact hook banner text",
      "recommended_y_pos": 250,
      "caption": "Engaging caption with CTA",
      "hashtags": "#niche1 #niche2 #viralreels ... (12-15 relevant hashtags)",
      "tone": "detected tone"
    }}
    """

    print("🤖 [Pass 1] Multimodal AI is extracting niche, punchline, and layout...")
    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[video_file, system_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
    except Exception as e:
        print(f"⚠️ [Pass 1] Retrying with backup model due to: {e}")
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=[video_file, system_prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )

    try:
        result = json.loads(response.text)
        print(f"✨ [AI Analysis] Niche: {result.get('detected_niche')} | Hook: '{result.get('hook_text')}' | Safe Y: {result.get('recommended_y_pos', 250)}")
        return result
    except Exception as e:
        print(f"⚠️ [Pass 1] Parsing fallback: {e}")
        return {
            "detected_niche": "General",
            "video_summary": "Short form video content.",
            "hook_text": "Wait for the end result 💀🔥",
            "recommended_y_pos": 250,
            "caption": "Save this reel for later! Follow for daily content 👇",
            "hashtags": "#reels #trending #viral #explore #fyp #dailycontent",
            "tone": "engaging"
        }
