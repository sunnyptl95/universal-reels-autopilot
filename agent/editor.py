import os
import subprocess
import shutil

def find_ffmpeg() -> str:
    """Finds ffmpeg path in system PATH or common system locations."""
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

def overlay_viral_hook(input_video: str, hook_text: str, output_video: str, y_pos: int = 240) -> str:
    """
    Overlays a high-contrast bold banner text hook at the calculated safe zone.
    Auto-wraps long text across 2 lines to prevent border clipping.
    """
    ffmpeg_exe = find_ffmpeg()
    os.makedirs(os.path.dirname(os.path.abspath(output_video)), exist_ok=True)
    
    # Clean hook text for FFmpeg filter safety
    safe_text = hook_text.replace("'", "").replace(":", " -").replace("%", " percent")
    
    # Auto-wrap text into 2 lines if longer than 34 characters
    if len(safe_text) > 34 and " " in safe_text:
        words = safe_text.split(" ")
        mid = len(words) // 2
        line1 = " ".join(words[:mid])
        line2 = " ".join(words[mid:])
        safe_text = f"{line1}\n{line2}"

    # Filterchain: drawtext with semi-transparent dark banner box
    filter_chain = (
        f"drawtext=font='Arial':text='{safe_text}':"
        f"fontcolor=white:fontsize=42:line_spacing=12:box=1:boxcolor=black@0.75:boxborderw=18:"
        f"x=(w-text_w)/2:y={y_pos}"
    )

    cmd = [
        ffmpeg_exe,
        "-y",
        "-i", input_video,
        "-vf", filter_chain,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "22",
        "-c:a", "copy",
        output_video
    ]

    print(f"🎬 [Editor] Applying hook banner at safe y={y_pos}: '{hook_text}'...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    if result.returncode != 0:
        print(f"⚠️ [Editor] FFmpeg error: {result.stderr[:300]}")
        shutil.copyfile(input_video, output_video)
        return output_video

    print(f"✅ [Editor] Edited reel ready at: {output_video}")
    return output_video
