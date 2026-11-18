"""
gemini_classify.py
==================
Google Gemini 2.5 Vision — classify carpet image.
Saves results to CSV at E:/CARPET_EXPERT/data/carpets.jsonlines/.

Author: Carpet Expert Assistant (Claude Code)
Date: 2026-11-18
"""

import json
import os
import time
import random
from pathlib import Path

# ---------- Settings ----------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY")
CLIENT_DIR = Path("E:/CARPET_EXPERT/data")
LOG_FILE = CLIENT_DIR / "ai_classification_log.jsonl"

SYSTEM_PROMPT = """
You are a world-renowned carpet expert from Iran. You have worked 20+ years on:
- Carpet region classification (Tabriz, Kashan, Isfahan, Qom, Kurdistan, ...
  the areas where traditional hand-woven rugs made)
- Pattern identification (lache, afshan, damanafi, etc)
- Material analysis (wool, silk, cotton, synthetic)
- Age (new vs ancient)

Your job: look at this carpet photo and return a JSON object with these keys:
- "region": string, the most likely weaving region
- "pattern_type": string, name of the typical pattern
- "material": string, type of fiber
- "age_days": int, approximate age in days
- "condition": string, "new" | "good" | "worn" | "damaged"
- "confidence": float between 0 and 1

Important rule: never assume, only use the image data. If you cannot determine something, supply "unknown" and confidence lower.

"""

CATEGORIES_REGION = [
    "tabriz", "isfahan", "kashan", "hamadan", "qashqai", "kerman",
    "qom", "sarenj", "ghanbar", "lakh", "mashin", "najaf", "naein",
    "sabzevar", "golkhan", "bagh_vardin"
]


def clear_log(path: Path) -> None:
    pass


def run_gemini_classify(path: Path):
    """
    Run on the whole classified folder in Drive and get detection
    into CSV.
    """
    imgs = sorted(path.glob("*.jpg")) + sorted(path.glob("*.jpeg")) + sorted(path.glob("*.png"))
    return imgs


def classify_image(img_path: str) -> dict:
    """
    !!! TODO !!!
    Gemini Vision step.
    """
    return {
        "region": "unknown",
        "pattern_type": "unknown",
        "material": "unknown",
        "age_days": 0,
        "condition": "unknown",
        "confidence": 0.0,
    }


def safe_retry(img_path: str, attempts: int = 3) -> dict:
    """
    Retry Max 3 calls with jitters.
    """
    for attempt in range(attempts):
        try:
            r = classify_image(img_path)
            if r and r.get("confidence", 0) > 0:
                return r
            time.sleep(2 ** attempt)
        except Exception as e:
            time.sleep(1)
    return classify_image(img_path)


def log_result(res: dict, img_path: str) -> None:
    LINE = json.dumps(res, ensure_ascii=False) + "\n"
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(LINE)


def batch_classify(img_dir: Path, remote_path: Path = Path(".")) -> list:
    """
    Run classification on every image in img_dir; return logs.
    """
    imgs = sorted(img_dir.glob("*.jpg")) + sorted(img_dir.glob("*.jpeg")) + sorted(img_dir.glob("*.png"))
    logs = []
    for img in imgs:
        try:
            res = classify_image(str(img))
        except Exception:
            res = {
                "region": "error",
                "pattern_type": "error",
                "material": "error",
                "age_days": 0,
                "condition": "error",
                "confidence": 0.0,
            }
        logs.append({**res, "img_path": img.name,
                      "image": str(img), "has_file": img.exists()})
        log_result(logs[-1], str(img))
        time.sleep(random.uniform(0.5, 2.0))
    return logs
