"""
price_calculator.py
===================
Pricing engine for Persian carpet estimates.
Build a weighted, lower/upper price range.

Author: Carpet Expert Assistant (Claude Code)
Date: 2026-11-18
"""

import csv
import re
from datetime import datetime

# ---------- Settings ----------
OUT_DIR = "E:/CARPET_EXPERT/data"
CARPET_PRICE_SHEET = "E:/CARPET_EXPERT/data/price_database.csv"


def strip_price(text: str) -> int:
    """'1,200,000 تومان' -> 1200000"""
    q = re.sub(r"[^\d]", "", str(text))
    return int(q) if q.isdigit() else 0


def price_region_base(region: str) -> float:
    """Base ratio of region typing."""
    return {
        "tabriz": 1.4,
        "isfahan": 1.3,
        "kashan": 1.3,
        "hamadan": 1.1,
        "qashqai": 1.0,
        "kerman": 1.0,
        "qom": 0.9,
        "nahavand": 0.9,
        "sarakhs": 0.8,
        "्लाख": 0.8,
        "sample": 0.5,
    }.get(region.lower(), 1.0)


def price_material_ratio(material: str) -> float:
    return {
        "silk": 2.0,
        "ابریکن": 2.0,
        "wool": 1.0,
        "cotton": 0.85,
        "nylon": 0.6,
        "sann": 0.7,
    }.get(material.lower(), 1.0)


def price_age_factor(date_csv: str, carpet_age_days: int) -> float:
    """Normalize age ratio from days."""
    return min(1.0 + (carpet_age_days / 365_000.0), 2.5)


def read_price_database(path: str = CARPET_PRICE_SHEET) -> list:
    """Read CSV of p_ tag."""
    rows = []
    if not os.path.isfile(path):
        return rows
    with open(path, "r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows


def estimate_price(carpet: dict) -> dict:
    """
    Estimated from `carpet` (dict with: region, material, age_days, size_m,
    knots etc.). Returns unit/low/high.
    """
    base_sqm = 1_000_000  # Toman per square meter base

    region_ratio = price_region_base(carpet.get("region", ""))
    material_ratio = price_material_ratio(carpet.get("material", "wool"))
    age_factor = price_age_factor(None, carpet.get("age_days", 0))
    size = float(carpet.get("size_m", 1.0))
    knots = float(carpet.get("knots", 100))
    size_factor = min(1.25, 1.0 + (size / 50))
    knot_factor = min(1.5, knots / 100.0)

    unit_price = base_sqm * region_ratio * material_ratio * age_factor \
        * size_factor * knot_factor

    low = round(unit_price * 0.7, -3)
    high = round(unit_price * 1.35, -3)

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "low تومان": low,
        "unit تومان": round(unit_price, -3),
        "high تومان": high,
        "region_ratio": region_ratio,
        "material_ratio": material_ratio,
        "age_factor": age_factor,
        "size_factor": size_factor,
    }
