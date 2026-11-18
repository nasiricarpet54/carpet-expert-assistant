"""
colab_scraper.py
================
Run on Google Colab.
Scrapes carpet images from Bing Images.
Saves to Drive: /carpet-raw/images/
Writes classification log: /carpet-raw/carpets_classification.csv
Uses Gemini 2.5 Pro Vision to classify.

Author: Carpet Expert Assistant (Claude Code)
Date: 2026-11-18
"""

import os
import re
import json
import time
import random
import urllib.request
import urllib.parse
from pathlib import Path

# ===== Configuration =====
DRIVE_MOUNT = "/content/drive"
GDRIVE_FOLDER = "carpet-raw"
STORAGE = Path(DRIVE_MOUNT) / GDRIVE_FOLDER / "images"
CSV_LOG = Path(DRIVE_MOUNT) / GDRIVE_FOLDER / "carpets_classification.csv"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

QUERIES = [
    "قالی تبریز ۶ متری",
    "فرش دستباف تبریز",
    "قالی قاشقائی ۹ متری",
    "فرش اصفهان ۶ متری",
    "قالی کاشان سنتی",
    "قالی مازندران",
    "فرش کرد دستباف",
    "carpet rug persian",
    "Persian carpet pattern",
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
)

# ===== Classes


def fetch_page(url: str, headers: dict = None, timeout: int = 30):
    """Fetch HTTP page."""
    if headers is None:
        headers = {"User-Agent": USER_AGENT}
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            time.sleep(2)
            print(f"[retry-{attempt+1}] Failed: {e}")
    return ""


def extract_bing_image_urls(html: str, max_images: int = 50):
    """Extract image URLs from Bing results."""
    urls = re.findall(r'md-src="(https?://[^"]+)"', html)
    urls = [u.replace("&amp;", "&") for u in urls]
    return [u for u in urls if u.endswith((".jpg", "jpeg", "png", "webp"))][:max_images]


def fetch_image_bytes(url: str):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.read()
    except Exception as e:
        return None


def resize_image(filepath: Path, size=(400, 400), quality=70):
    """Resize image by Pillow."""
    from PIL import Image
    try:
        img = Image.open(filepath)
        img = img.convert("RGB")
        img.thumbnail(size, Image.Resampling.LANCZOS)
        img.save(filepath, "JPEG", quality=quality, optimize=True)
        return True
    except Exception as e:
        print(f"Resizing error {filepath}: {e}")
        return False


def query_bing_images(query: str):
    base = "https://www.bing.com/images/search?q="
    return f"{base}{urllib.parse.quote(query)}&first=0&count=50"


def scrape_images(query: str, out_dir: Path, max_images: int = 10):
    """Download images to dir."""
    out_dir.mkdir(parents=True, exist_ok=True)
    friendly = query.replace(" ", "_")
    downloaded = []
    html = fetch_page(query_bing_images(query))
    if not html:
        return []
    for img_url in extract_bing_image_urls(html, max_images):
        data = fetch_image_bytes(img_url)
        if not data:
            continue
        name = f"{friendly}_{len(downloaded)+1}.jpg"
        path = out_dir / name
        path.write_bytes(data)
        downloaded.append((name, img_url, path))
        resize_image(path, (400, 400), 70)
        time.sleep(random.uniform(1.5, 4.0))
    return downloaded


def save_classification_log(row):
    """Append CSV."""
    import csv
    if not row.get("region"):
        row["region"] = "unknown"
    try:
        if not os.path.exists(CSV_LOG):
            with open(CSV_LOG, "w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["image_path", "query", "url", "status", "region", "pattern", "confidence"])
                w.writeheader()
        with open(CSV_LOG, "a", newline="", encoding="utf-8") as f:
            csv.DictWriter(f, fieldnames=["image_path", "query", "url", "status", "region", "pattern", "confidence"]).writerow(row)
    except Exception as e:
        print(f"CSV write error: {e}")


def classify_with_gemini(path: Path) -> dict:
    """Call Gemini 2.5 Pro Vision API."""
    if not GEMINI_API_KEY:
        return {"region": "no-api-key", "pattern": "unknown", "confidence": 0.0, "note": "Gemini API key required"}
    import base64
    from google.api_core.exceptions import GoogleAPICallError
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel("gemini-2.5-pro")
        with open(path, "rb") as f:
            data = f.read()
        text = f"""Analyze this Persian carpet image. Return a JSON with keys:
- region: from [tabriz, qashqai, isfahan, kashan, hezaran, kerman, qom, baniband, najaf, semnan, draw, mianeh, mashin, lavasan, golkhan, baghvard, roshan, sarustan, naein, varam, hamadan]
- pattern: string
- material: string
- confidence: float 0-1

"region" must be lowercase."""
        resp = model.generate_content([data, text])
        out = {}
        try:
            out = json.loads(resp.text)
        except Exception:
            # Try extracting JSON
            m = re.search(r"\{.*\}", resp.text)
            if m:
                out = json.loads(m.group(0))
        return out
    except Exception as e:
        print(f"GC error: {e}")
        return {"region": "error", "pattern": "unknown", "confidence": 0.0}


def run():
    """Main loop."""
    print("Scrape images...")
    skate = []
    for query in QUERIES[:3]:
        print(f"> Query: {query}")
        d = scrape_images(query, STORAGE)
        for name, url, path in d:
            print(f"  -> {name}")
            res = classify_with_gemini(path)
            save_classification_log({
                "image_path": str(path),
                "query": query,
                "url": url,
                "status": "classified",
                "region": res.get("region", "unknown"),
                "pattern": res.get("pattern", "unknown"),
                "confidence": res.get("confidence", 0.0),
            })
        skate.extend(d)
        time.sleep(30)
    print(f"Total: {len(skate)}")
    return skate


if __name__ == "__main__":
    run()
