import os
import random
import datetime
from typing import List

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from moviepy.editor import TextClip, ColorClip, CompositeVideoClip

# ---------- BASIC CONFIG ----------

OUTPUT_DIR = "videos"
os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="YouTube Shorts Automation")

# Some simple topics – you can expand this list
MOTIVATION_TOPICS = [
    "overcoming failure",
    "discipline vs motivation",
    "starting small",
    "consistency",
    "self-belief",
    "time management",
    "handling distractions",
]

SCIENCE_TOPICS = [
    "neuroplasticity of the brain",
    "placebo effect",
    "circadian rhythm",
    "black holes",
    "CRISPR gene editing",
    "evolution of antibiotic resistance",
    "photosynthesis",
]

# ---------- SCRIPT GENERATION (very simple, no external AI) ----------

def generate_motivation_script(topic: str) -> str:
    templates = [
        f"Most people underestimate the power of small steps. When it comes to {topic}, the real game-changer is consistency. "
        "You do not need perfect conditions, you just need to start. 30 minutes today is better than 0 minutes waiting for the 'right time'.",

        f"When you feel like giving up on {topic}, remember this: discomfort is temporary, but regret is permanent. "
        "Future you is watching the choices you make today. Do one hard thing now, just for them.",

        f"{topic.title()} is not about talent, it is about habits. Build tiny daily actions around your goal. "
        "Habits remove the need for motivation. Once it is a habit, it becomes automatic."
    ]
    return random.choice(templates)


def generate_science_script(topic: str) -> str:
    templates = [
        f"Let us talk about {topic}. In simple words, it shows how complex systems in our body or the universe follow clear rules. "
        "We often think science is complicated, but it is really about patterns. Once you see the pattern, the topic becomes easier.",

        f"{topic.title()} sounds complex, but here is the idea: science breaks big mysteries into small, testable questions. "
        "This is exactly how you should study. Turn a big scary chapter into tiny questions and solve one at a time.",

        f"Here is a quick thought about {topic}. Behind every big discovery, there were years of failed experiments. "
        "Science is basically organized failure. Each failure gives data, and that data leads to understanding."
    ]
    return random.choice(templates)


def create_script(kind: str) -> str:
    if kind == "motivation":
        topic = random.choice(MOTIVATION_TOPICS)
        return generate_motivation_script(topic)
    elif kind == "science":
        topic = random.choice(SCIENCE_TOPICS)
        return generate_science_script(topic)
    else:
        raise ValueError("Unknown kind")


# ---------- VIDEO GENERATION (TEXT-ONLY VERTICAL SHORT) ----------

def generate_video_from_text(text: str, filename: str, duration: int = 30) -> str:
    """
    Creates a simple 1080x1920 vertical video with text.
    """
    width, height = 1080, 1920

    # Background
    bg_clip = ColorClip(size=(width, height), color=(20, 20, 40))
    bg_clip = bg_clip.set_duration(duration)

    # Text: wrap into multiple lines (simple split)
    max_chars_per_line = 40
    words = text.split()
    lines = []
    current_line = []

    for w in words:
        if len(" ".join(current_line + [w])) <= max_chars_per_line:
            current_line.append(w)
        else:
            lines.append(" ".join(current_line))
            current_line = [w]
    if current_line:
        lines.append(" ".join(current_line))

    final_text = "\n".join(lines)

    txt_clip = TextClip(
        final_text,
        fontsize=60,
        font="Arial",
        method="caption",
        size=(width - 200, None)
    ).set_position(("center", "center")).set_duration(duration)

    video = CompositeVideoClip([bg_clip, txt_clip])
    output_path = os.path.join(OUTPUT_DIR, filename)
    video.write_videofile(output_path, fps=30, codec="libx264", audio=False)

    return output_path


# ---------- MAIN AUTOMATION ENDPOINT ----------

@app.get("/")
def root():
    return {"status": "ok", "message": "YouTube shorts automation is running."}


@app.get("/run-daily")
def run_daily(secret: str = Query(...)):
    """
    This endpoint will be called 3x/day by an external cron service.

    We keep a simple ?secret=YOUR_SECRET so random people cannot trigger it.
    """

    # Basic security
    expected = os.environ.get("RUN_SECRET", "changeme")
    if secret != expected:
        raise HTTPException(status_code=403, detail="Forbidden")

    created_files: List[str] = []

    # 3 shorts: mix of motivation and science
    kinds = ["motivation", "science", "motivation"]

    for kind in kinds:
        script = create_script(kind)
        now = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{kind}_{now}.mp4"
        path = generate_video_from_text(script, filename)
        created_files.append(path)

        # Here in future you will call your YouTube upload function

    return JSONResponse({"status": "ok", "created": created_files})
