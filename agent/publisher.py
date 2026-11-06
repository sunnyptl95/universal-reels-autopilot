import os
import json
import requests
import cloudinary
import cloudinary.uploader

BUFFER_GRAPHQL_URL = "https://api.buffer.com/graphql"
MAX_BUFFER_FREE_TIER_QUEUE = 10

def init_cloudinary():
    """
    Bulletproof Cloudinary initialization:
    - Strips whitespace & quotes from secrets.
    - Auto-detects if user swapped Key and Secret.
    """
    cloudinary_url = os.getenv("CLOUDINARY_URL")
    if cloudinary_url:
        cloudinary.config(cloudinary_url=cloudinary_url.strip(), secure=True)
        return

    cloud_name = (os.getenv("CLOUDINARY_CLOUD_NAME") or "").strip().strip('"').strip("'")
    api_key = (os.getenv("CLOUDINARY_API_KEY") or "").strip().strip('"').strip("'")
    api_secret = (os.getenv("CLOUDINARY_API_SECRET") or "").strip().strip('"').strip("'")

    # Auto-detect if user swapped numeric API key with alphanumeric secret
    if api_key and not api_key.isdigit() and api_secret.isdigit():
        print("🔄 [Cloudinary] Swapped Key and Secret detected, auto-fixing...")
        api_key, api_secret = api_secret, api_key

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True
    )

def upload_video_to_cloudinary(local_video_path: str) -> str:
    """Uploads local video to Cloudinary and returns high-speed HTTPS CDN URL."""
    init_cloudinary()
    print(f"☁️ [Cloudinary] Uploading edited video: {os.path.basename(local_video_path)}...")
    res = cloudinary.uploader.upload_large(
        local_video_path,
        resource_type="video",
        folder="instagram_reels"
    )
    url = res.get("secure_url")
    print(f"✅ [Cloudinary] Video hosted at: {url}")
    return url

def get_buffer_queue_count(token: str, org_id: str) -> int:
    """Checks current queue size to respect Buffer free-tier limit of 10 scheduled posts."""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    query = """
    query {
      posts(input: { organizationId: "%s" }) {
        edges {
          node {
            id
            status
          }
        }
      }
    }
    """ % org_id

    try:
        res = requests.post(BUFFER_GRAPHQL_URL, json={"query": query}, headers=headers).json()
        posts = res.get("data", {}).get("posts", {}).get("edges", [])
        return len(posts)
    except Exception as e:
        print(f"⚠️ [Buffer] Queue count query note: {e}")
        return 0

def publish_reel_to_buffer(video_path: str, caption: str, mode: str = "addToQueue") -> dict:
    """
    Checks Buffer free-tier 10-post limit, uploads video to Cloudinary,
    and schedules Reel in Buffer queue.
    """
    token = os.getenv("BUFFER_ACCESS_TOKEN")
    channel_id = os.getenv("BUFFER_CHANNEL_ID")
    org_id = os.getenv("BUFFER_ORG_ID")

    if not token or not channel_id:
        print("⚠️ [Buffer] Credentials missing.")
        return {"success": False, "error": "BUFFER credentials missing"}

    # 1. Enforce Buffer Free Tier 10 Post Limit Check
    if org_id:
        current_count = get_buffer_queue_count(token, org_id)
        print(f"📊 [Buffer Queue Check] Current scheduled posts: {current_count}/{MAX_BUFFER_FREE_TIER_QUEUE}")
        if current_count >= MAX_BUFFER_FREE_TIER_QUEUE:
            msg = f"Buffer Queue Full ({current_count}/10 limit reached). Pausing new additions until older posts publish."
            print(f"⏸️ [Buffer] {msg}")
            return {"success": False, "queue_full": True, "error": msg}

    # 2. Upload to Cloudinary for fast CDN access
    if os.path.exists(video_path):
        video_url = upload_video_to_cloudinary(video_path)
    else:
        video_url = video_path

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    mutation = """
    mutation CreateReel($input: CreatePostInput!) {
      createPost(input: $input) {
        ... on PostActionSuccess {
          post {
            id
            status
            text
          }
        }
        ... on InvalidInputError {
          message
        }
        ... on UnexpectedError {
          message
        }
        ... on LimitReachedError {
          message
        }
      }
    }
    """

    variables = {
        "input": {
            "channelId": channel_id,
            "schedulingType": "automatic",
            "mode": mode,
            "text": caption,
            "assets": [
                {
                    "video": {
                        "url": video_url,
                        "metadata": {
                            "thumbnailOffset": 2000
                        }
                    }
                }
            ],
            "metadata": {
                "instagram": {
                    "type": "reel",
                    "shouldShareToFeed": True
                }
            }
        }
    }

    print(f"🚀 [Buffer] Sending Reel to Buffer Queue ({channel_id})...")
    res = requests.post(BUFFER_GRAPHQL_URL, json={"query": mutation, "variables": variables}, headers=headers).json()
    post_data = res.get("data", {}).get("createPost", {})
    
    if "post" in post_data:
        post_id = post_data["post"]["id"]
        status = post_data["post"]["status"]
        print(f"🎉 [Buffer] Reel successfully scheduled! Post ID: {post_id}")
        return {
            "success": True,
            "post_id": post_id,
            "status": status,
            "permalink": f"https://publish.buffer.com/channels/{channel_id}"
        }
    else:
        err = post_data.get("message", json.dumps(res))
        print(f"❌ [Buffer] Failed: {err}")
        return {"success": False, "error": err}
