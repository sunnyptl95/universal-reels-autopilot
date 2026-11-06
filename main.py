"""
========================================================================
UNIVERSAL INSTAGRAM REELS AUTOPILOT (ZERO-PROMPT ARCHITECTURE)
Conceived & Architected by: Sunny Patel (@sunnyptl95)
Engineered with: Antigravity AI (Google DeepMind)
========================================================================
"""

import os
import json
import datetime
from dotenv import load_dotenv

from agent.analyzer import analyze_video_and_generate_hooks
from agent.editor import overlay_viral_hook
from agent.quality_checker import verify_edited_video_quality
from agent.publisher import publish_reel_to_buffer, get_buffer_queue_count, MAX_BUFFER_FREE_TIER_QUEUE
from agent.learner import audit_viral_performance_and_learn
from agent.telegram_bot import send_telegram_alert
from agent.drive_manager import get_next_unposted_reel

def run_autopilot_cycle():
    """
    Main Universal Orchestrator:
    1. Buffer queue check (10-post free tier limit guard)
    2. Deep Self-Learning diagnostic
    3. Auto-pull unposted video from user's Google Drive folder
    4. Pass 1: Multimodal AI watches video, auto-detects niche, punchline, and safe Y-zone
    5. Safe overlay: Video editor draws high-contrast banner with auto text-wrap
    6. Pass 2: AI Visual QA ensures faces and core action are NOT obscured
    7. Publish: Uploads via Cloudinary CDN and schedules to Instagram via Buffer
    8. Updates history.json & dispatches mobile Telegram notification with video preview
    """
    load_dotenv()
    print("=" * 65)
    print(f"🚀 [Universal Autopilot] Starting Cycle at {datetime.datetime.now().isoformat()}")
    print("=" * 65)

    token = os.getenv("BUFFER_ACCESS_TOKEN")
    org_id = os.getenv("BUFFER_ORG_ID")

    # Step 1: Buffer Free Tier 10-Post Safeguard
    if token and org_id:
        queue_count = get_buffer_queue_count(token, org_id)
        print(f"📊 [Buffer Queue Check] Current scheduled queue: {queue_count}/{MAX_BUFFER_FREE_TIER_QUEUE}")
        if queue_count >= MAX_BUFFER_FREE_TIER_QUEUE:
            msg = (
                f"⏸️ *Buffer Queue Status: 10/10 Limit Reached*\n\n"
                f"Queue is full ({queue_count}/10). Autopilot is paused until scheduled reels are posted to Instagram!"
            )
            print(f"⏸️ [Buffer Guard] {msg}")
            send_telegram_alert(msg)
            return

    # Step 2: Self-Learning (Diagnosing Viral vs Flop factors)
    print("\n[Step 2/7] Running Self-Learning & Viral Strategy Diagnosis...")
    memory, audit_report = audit_viral_performance_and_learn(history_path="history.json", memory_path="memory.json")
    if audit_report:
        send_telegram_alert(audit_report)

    # Step 3: Fetch next unposted video from Google Drive
    print("\n[Step 3/7] Fetching next unposted reel from Google Drive...")
    reel_info = get_next_unposted_reel(history_path="history.json", temp_folder="temp_downloads")
    if not reel_info:
        print("🎉 [Agent] All reels have been posted! No pending videos found in Google Drive.")
        send_telegram_alert("⚠️ *Autopilot Alert:* All reels in your Google Drive folder have been posted!")
        return

    raw_video_path = reel_info["local_path"]
    filename = reel_info["filename"]
    print(f"🎯 [Agent] Selected Video: {filename}")

    # Step 4: Pass 1 - Multimodal Niche & Visual Safe-Zone Analysis
    print("\n[Step 4/7] Pass 1: Multimodal AI analyzing niche, dialogues & safe placement...")
    analysis = analyze_video_and_generate_hooks(raw_video_path, memory_context=memory)
    
    niche = analysis.get("detected_niche", "General")
    hook_text = analysis.get("hook_text", "Wait for the end result 💀🔥")
    caption = analysis.get("caption", "Save this reel and share with a friend! 👇")
    hashtags = analysis.get("hashtags", "#reels #trending #viral #fyp")
    safe_y_pos = analysis.get("recommended_y_pos", 250)
    
    full_caption = f"{caption}\n\n.\n.\n{hashtags}"

    # Step 5: Render Video with Viral Banner at Safe Zone
    print(f"\n[Step 5/7] Rendering hook banner at safe y={safe_y_pos}...")
    os.makedirs("processed_output", exist_ok=True)
    edited_video_path = os.path.join("processed_output", f"hook_{filename}")
    overlay_viral_hook(raw_video_path, hook_text, edited_video_path, y_pos=safe_y_pos)

    # Step 6: Pass 2 - AI Visual QA Inspection (Face Overlap Protection)
    print("\n[Step 6/7] Pass 2: AI inspecting edited frame for face overlap & legibility...")
    qa_result = verify_edited_video_quality(edited_video_path, hook_text)
    qa_score = qa_result.get("legibility_score_out_of_10", 10)
    qa_feedback = qa_result.get("feedback", "Placement is clean!")
    faces_covered = qa_result.get("faces_covered", False)

    # Self-healing safeguard: if faces covered or QA score low, adjust or fallback
    final_video_to_publish = edited_video_path
    if faces_covered or qa_score < 6:
        print(f"⚠️ [QA Alert] Faces obstructed (Score: {qa_score}). Repositioning higher...")
        adjusted_y = max(170, safe_y_pos - 80)
        overlay_viral_hook(raw_video_path, hook_text, edited_video_path, y_pos=adjusted_y)
        recheck = verify_edited_video_quality(edited_video_path, hook_text)
        if recheck.get("faces_covered", False):
            print("⚠️ [QA Protection] Using original clean video to preserve aesthetic quality.")
            final_video_to_publish = raw_video_path
            qa_feedback = "Original video retained (Prevented face overlap)"
            qa_score = 10
        else:
            qa_score = recheck.get("legibility_score_out_of_10", 9)
            qa_feedback = "Re-adjusted hook banner safely"

    # Step 7: Schedule Reel to Instagram via Buffer (Cloudinary CDN bridge)
    print("\n[Step 7/7] Scheduling Reel to Instagram via Buffer...")
    publish_result = publish_reel_to_buffer(final_video_to_publish, full_caption, mode="addToQueue")
    
    if publish_result.get("queue_full"):
        send_telegram_alert(
            f"⏸️ *Buffer Queue Status: 10/10 Limit Reached*\n\n"
            f"Free tier queue is full. The agent will automatically schedule next reel once older reels publish!"
        )
        return

    permalink = publish_result.get("permalink", "https://publish.buffer.com")

    # Step 8: Log in history
    history_file = "history.json"
    if not os.path.exists(history_file):
        history_data = {"uploaded_reels": []}
    else:
        with open(history_file, "r", encoding="utf-8") as f:
            history_data = json.load(f)

    record = {
        "filename": filename,
        "niche": niche,
        "posted_at": datetime.datetime.now().isoformat(),
        "hook_text": hook_text,
        "qa_score": qa_score,
        "post_id": publish_result.get("post_id"),
        "status": publish_result.get("status"),
        "permalink": permalink,
        "caption": caption,
        "hashtags": hashtags
    }
    history_data.setdefault("uploaded_reels", []).append(record)
    history_data["last_run_timestamp"] = datetime.datetime.now().isoformat()

    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(history_data, f, indent=2)

    # Step 9: Send Telegram Notification with Video Preview
    telegram_msg = (
        f"🎬 *New Reel Scheduled on Autopilot!*\n\n"
        f"🏷️ *Detected Niche:* `{niche}`\n"
        f"📌 *Hook:* `{hook_text}`\n"
        f"🔍 *Visual QA:* Score {qa_score}/10 ({qa_feedback})\n"
        f"📝 *Caption:* {caption}\n\n"
        f"🏷️ *Hashtags:* {hashtags}\n\n"
        f"🔗 *Buffer Queue:* [View Queue]({permalink})\n"
        f"📊 *Total Reels Scheduled:* {len(history_data['uploaded_reels'])}"
    )
    send_telegram_alert(telegram_msg, video_path=final_video_to_publish)

    # Step 10: Cleanup temp files to save disk space
    try:
        if reel_info.get("source") == "google_drive" and os.path.exists(raw_video_path):
            os.remove(raw_video_path)
        if os.path.exists(edited_video_path):
            os.remove(edited_video_path)
    except Exception as e:
        print(f"Cleanup note: {e}")

    print("\n✅ [Universal Autopilot] Cycle Completed Successfully!\n")

if __name__ == "__main__":
    run_autopilot_cycle()
