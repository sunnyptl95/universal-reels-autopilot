import os
import json
import gdown

def get_next_unposted_reel(history_path: str = "history.json", temp_folder: str = "temp_downloads") -> dict:
    """
    Connects to the user's Google Drive folder from environment variables,
    identifies the next unposted .mp4 video, and downloads ONLY that single video.
    """
    posted_files = set()
    if os.path.exists(history_path):
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
            for item in history.get("uploaded_reels", []):
                posted_files.add(item.get("filename"))

    folder_url = os.getenv("GDRIVE_FOLDER_URL")
    folder_id = os.getenv("GDRIVE_FOLDER_ID")

    if not folder_url and folder_id:
        folder_url = f"https://drive.google.com/drive/folders/{folder_id}"

    if not folder_url:
        print("⚠️ [DriveManager] Neither GDRIVE_FOLDER_URL nor GDRIVE_FOLDER_ID is set in environment secrets!")
        # Check if local reels_input has fallback videos
        if os.path.exists("reels_input"):
            for f in os.listdir("reels_input"):
                if f.lower().endswith(".mp4") and f not in posted_files:
                    return {
                        "filename": f,
                        "local_path": os.path.join("reels_input", f),
                        "source": "local_folder"
                    }
        return None

    print(f"📁 [DriveManager] Scanning Google Drive folder for next unposted video...")
    try:
        files = gdown.download_folder(url=folder_url, quiet=True, skip_download=True)
    except Exception as e:
        print(f"⚠️ [DriveManager] Error scanning Drive: {e}")
        files = []

    # Filter for .mp4 files
    mp4_files = [f for f in files if f.path.lower().endswith(".mp4")]
    mp4_files.sort(key=lambda x: x.path)

    for item in mp4_files:
        if item.path not in posted_files:
            print(f"🎯 [DriveManager] Found next reel: '{item.path}' (Drive ID: {item.id})")
            os.makedirs(temp_folder, exist_ok=True)
            local_target = os.path.join(temp_folder, item.path)
            
            # Download only this single file
            if not os.path.exists(local_target):
                print(f"⬇️ [DriveManager] Downloading single video from Google Drive (~5-15MB)...")
                gdown.download(id=item.id, output=local_target, quiet=False)

            return {
                "filename": item.path,
                "local_path": local_target,
                "drive_id": item.id,
                "source": "google_drive"
            }

    # Fallback to local reels_input
    if os.path.exists("reels_input"):
        for f in os.listdir("reels_input"):
            if f.lower().endswith(".mp4") and f not in posted_files:
                return {
                    "filename": f,
                    "local_path": os.path.join("reels_input", f),
                    "source": "local_folder"
                }

    return None
