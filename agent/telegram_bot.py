import os
import requests

def send_telegram_alert(message: str, video_path: str = None):
    """Sends status message and optional video preview to user's Telegram."""
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")

    if not bot_token or not chat_id:
        print("ℹ️ [Telegram] No credentials provided, skipping Telegram alert.")
        return

    # 1. Send Text message
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "Markdown",
            "disable_web_page_preview": False
        }
        res = requests.post(url, json=payload, timeout=10).json()
        if res.get("ok"):
            print("📱 [Telegram] Notification delivered to mobile.")
        else:
            print(f"⚠️ [Telegram] Error: {res}")
    except Exception as e:
        print(f"⚠️ [Telegram] Failed to send text: {e}")

    # 2. Send Video preview if provided
    if video_path and os.path.exists(video_path):
        try:
            print(f"📱 [Telegram] Sending video preview to Telegram ({os.path.basename(video_path)})...")
            video_url = f"https://api.telegram.org/bot{bot_token}/sendVideo"
            with open(video_path, "rb") as video_file:
                files = {"video": video_file}
                data = {"chat_id": chat_id, "caption": "🎬 *Reel Scheduled Preview*"}
                v_res = requests.post(video_url, data=data, files=files, timeout=60).json()
                if v_res.get("ok"):
                    print("📱 [Telegram] Video preview sent successfully!")
                else:
                    print(f"⚠️ [Telegram] Video send note: {v_res}")
        except Exception as e:
            print(f"⚠️ [Telegram] Video send exception: {e}")
