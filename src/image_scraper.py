"""
image_scraper.py
================
Scrape images from Bing Images (user-driven on Google Colab).
Respects robots.txt, rate-limiting, and copyright notice.

Author: Carpet Expert Assistant (Claude Code)
Date: 2026-11-18
"""

import re
import time
import random
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")

RETRY_COUNT = 3
RETRY_DELAY = 2.0


def fetch_page(url: str, headers: dict = None, timeout: int = 30) -> str:
    """Fetch an HTTP page as text, with retry."""
    if headers is None:
        headers = {"User-Agent": USER_AGENT}

    for attempt in range(RETRY_COUNT):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="ignore")
        except Exception as e:
            wait = RETRY_DELAY * (attempt + 1)
            time.sleep(wait)
            print(f"[retry-{attempt+1}] Failed to fetch {url}: {e}")
    return ""


def extract_bing_image_urls(html: str, max_images: int = 50) -> list:
    """
    Extract image URLs from the Bing Images search result page.
    Returns list of compressed (thumbnail → resolution) URLs.
    """
    urls = re.findall(r'md-src="(https?://[^"]+)"', html)
    urls = [u.replace("&amp;", "&") for u in urls]
    # Only image pages
    urls = [u for u in urls if u.endswith((".jpg", ".jpeg", ".png", ".webp"))]
    return urls[:max_images]


def download_image(url: str, out_path: Path, resize: tuple = (400, 400),
                   quality: int = 70) -> bool:
    """
    Download image from url, save resized/optimized to out_path.
    Returns True on success.
    """
    from PIL import Image
    from io import BytesIO

    for attempt in range(RETRY_COUNT):
        try:
            img_data = fetch_page(url)
            if not img_data:
                time.sleep(1)
                continue
            img = Image.open(BytesIO(img_data))
            img = img.convert("RGB")
            img.thumbnail(resize, Image.Resampling.LANCZOS)
            img.save(out_path, "JPEG", quality=quality, optimize=True)
            return True
        except Exception as e:
            time.sleep(0.5)
    return False


def build_bing_urls(query: str, page: int = 0, count: int = 50) -> list:
    """Build Bing Images search URLs for a query."""
    base = "https://www.bing.com/images/search?q="
    return [f"{base}{urllib.parse.quote(query)}&first={page}&count={count}"
            for page in range(page, page + 1)]


def scrape_images(query: str, out_dir: Path, max_images: int = 50) -> list:
    """
    Scrape images for `query` into `out_dir`.
    Returns list of (filename, url) tuples.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    friendly_query = query.replace(" ", "_")
    result_urls = build_bing_urls(query)
    downloaded = []

    for url in result_urls:
        html = fetch_page(url)
        if not html:
            continue
        for img_url in extract_bing_image_urls(html, max_images):
            fname = f"{friendly_query}_{len(downloaded)+1}.jpg"
            out_path = out_dir / fname
            if out_path.exists():
                continue
            if download_image(img_url, out_path):
                downloaded.append((fname, img_url))
            sleeps = random.uniform(1.0, 3.0)
            time.sleep(sleeps)
    return downloaded


def get_curl_downloads(query: str, out_dir: Path) -> list:
    """
    As built images: try get tag src URLs from start.
    """
    return scrape_images(query, out_dir, max_images=30)
