import os
import json
from google import genai

def audit_viral_performance_and_learn(history_path: str = "history.json", memory_path: str = "memory.json") -> tuple:
    """
    Universal Self-Learning Engine:
    Examines previous post history, diagnoses winning viral hooks vs flop risks,
    and formulates rules for the next scheduled reel.
    """
    if not os.path.exists(memory_path):
        memory = {
            "learnings": [],
            "viral_reasons": [
                "Clear high-contrast hook text in first 2 seconds stops infinite scrolling",
                "Relatable situational conflicts trigger maximum friend tags and shares"
            ],
            "flop_reasons": [
                "Slow opening with no visual or emotional hook in first 3s",
                "Captions without a clear call-to-action reduce comment engagement"
            ]
        }
    else:
        with open(memory_path, "r", encoding="utf-8") as f:
            memory = json.load(f)

    if not os.path.exists(history_path):
        return memory, None

    with open(history_path, "r", encoding="utf-8") as f:
        history = json.load(f)

    uploaded_reels = history.get("uploaded_reels", [])
    if len(uploaded_reels) == 0:
        return memory, None

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return memory, None

    client = genai.Client(api_key=api_key)

    recent_posts_context = [
        {
            "hook": r.get("hook_text"),
            "caption": r.get("caption"),
            "niche": r.get("niche"),
            "qa_score": r.get("qa_score"),
            "date": r.get("posted_at")
        }
        for r in uploaded_reels[-5:]
    ]

    diagnosis_prompt = f"""
    You are an expert Instagram Reels algorithm scientist.
    Analyze the recently published reels performance context:
    {json.dumps(recent_posts_context, indent=2)}

    Determine:
    1. VIRAL DRIVERS: What elements ensure viral retention & shares for these niches?
    2. FLOP RISKS: What mistakes should be avoided in upcoming reels?
    3. GOLDEN RULE: 1 actionable directive for the next video.

    Respond in JSON:
    {{
      "why_viral_factors": ["Factor 1", "Factor 2"],
      "why_flop_reasons": ["Risk 1", "Risk 2"],
      "golden_rule_for_next_reel": "Rule for next reel"
    }}
    """

    try:
        ai_res = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=diagnosis_prompt,
            config={"response_mime_type": "application/json"}
        )
        diagnosis = json.loads(ai_res.text)
        
        rule = diagnosis.get("golden_rule_for_next_reel")
        if rule and rule not in memory.get("learnings", []):
            memory.setdefault("learnings", []).append(rule)
            memory["learnings"] = memory["learnings"][-10:]

        if diagnosis.get("why_viral_factors"):
            memory["viral_reasons"] = diagnosis.get("why_viral_factors")
        if diagnosis.get("why_flop_reasons"):
            memory["flop_reasons"] = diagnosis.get("why_flop_reasons")

        with open(memory_path, "w", encoding="utf-8") as f:
            json.dump(memory, f, indent=2)

        audit_report = (
            f"🧠 *Autopilot Self-Learning Diagnostic:*\n\n"
            f"🔥 *Winning Viral Triggers:*\n" +
            "\n".join(f"• {f}" for f in memory.get("viral_reasons", [])[:2]) + "\n\n"
            f"⚠️ *Flop Risks (Avoided):*\n" +
            "\n".join(f"• {r}" for r in memory.get("flop_reasons", [])[:2]) + "\n\n"
            f"🎯 *Next Video Strategy:* {rule}"
        )
        return memory, audit_report

    except Exception as e:
        print(f"⚠️ [Learner] Diagnosis note: {e}")
        return memory, None
