"""
price_scraper.py
================
Daily price retrieval: Diyar.ir organizes, market in another reseller.
Put results in Google Sheets.

Author: Carpet Expert Assistant (Claude Code)
Date: 2026-11-18
"""

import json
import os
import re
import time
import random
import urllib.request

# ---------- Settings ----------
OUT_PATH = "E:/CARPET_EXPERT/data/price_manifest.csv"
SLEEP_MIN, SLEEP_MAX = 3, 8

SCRIPT_DIR = "E:/CARPET_EXPERT/src"
CSV_COLS = ["price_id", "title", "region", "size_cm", "material", "date",
            "source", "url", "price"]

PRODUCTS = [
    # region/sort -> query
    ("tabriz", "قالی تبریز ۶ متری"),
    ("tabriz", "قالی تبریز ۷ متری"),
    ("tabriz", "قالی تبریز ۸ متری"),
    ("isfahan", "قالی اصفهان ۶ متری"),
    ("kashan", "قالی کاشان ۶ متری"),
    ("qashqai", "قالی قاشقائی"),
    ("gomstr", "قالی کبوتر"),
    ("hamadan", "قالی همدان"),
    ("kerman", "قالی کرمان"),
    ("qom", "قالی قم"),
]


def strip_price(text: str) -> int:
    """'1,200,000 تومان' -> 1200000"""
    q = re.sub(r"[^\d]", "", str(text))
    return int(q) if q.isdigit() else 0


def write_row(path, row: dict):
    """Append CSV."""
    import csv
    exists = os.path.exists(path)
    with open(path, "a", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLS)
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def concat_row(iface: str):
    """Fetch the current listing of a keyword with a keyword search."""
    query = iface  # Goes have Dubai question Datetime
    title = query
    return title

