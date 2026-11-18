# 🏵️ دستیار کارشناسی فرش — Carpet Expert Assistant

[![License](https://img.shields.io/badge/license-AGPLv3-blue)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://python.org)
[![Google](https://img.shields.io/badge/Google%20Cloud-Free-green)](https://cloud.google.com)
[![Status](https://img.shields.io/badge/status-MVP-amber)]()

## 🌐 معرفی

این پروژه یک **سامانه دستیار هوشمند** برای **کارشناسان رسمی دادگستری (رشته فرش)** است. هدف آن برنامه‌ریزی و کمک به ارزیابی فرش‌های دست‌باف است — نه جایگزین قاضی.

### قابلیت اصلی
1. **تشخیص تصویر:** محل بافت + نوع نقشه از روی تصویر فرش
2. **قیمت‌گذاری:** تخمین قیمت روز/تاریخی بر اساس اطلاعات کامل فرش

### ⚠️ Sancta Sancis
- **هیچ خروجی Auto یک تصمیم نیست.** هر نتیجه باید با تأیید کارشناس روبرو شود.
- **Audit Trail:** هر تخمین با timestamp + ID کاربر ذخیره می‌شود.

---

## 📁 ساختار پروژه

```
E:\CARPET_EXPERT\
├── docs/                    ← مستندات کامل
│   ├── ARCHITECTURE.md      ← معماری ۵ فاز
│   ├── IMAGE_PRICE_SCRAPE.md← لایه جمع‌آوری خودکار
│   ├── SCRAPER_ARCHITECTURE.md ← مستند فنی
│   └── SUMMARY_F.md         ← خلاصه اجرایی
├── src/
│   ├── appsscript/          ← Web App (Google Apps Script)
│   │   ├── code.gs          ← فرم آپلود + Gemini + Sheets
│   │   └── index.html       ← رابط کاربری
│   ├── image_scraper.py     ← CLI scraper (Bing Images)
│   ├── price_scraper.py     ← جمع‌آوری قیمت دیوار/شیپور
│   ├── price_calculator.py  ← Pricing engine ✅ تست شده
│   ├── gemini_classify.py   ← Gemini Vision classification
│   ├── colab_scraper.py     ← Scraping Colab + Drive
│   └── setup_colab.ipynb    ← Google Colab notebook
├── data/                    ← خروجی‌های داینامیک (ignored)
├── .gitignore
├── SETUP_INSTRUCTIONS.md
└── README.md
```

---

## 🚀 Installation & Setup

### ۱. Requirements

| ابزار | لینک | توضیح |
|------|------|-------|
| Google Account | https://google.com | برای Drive/Sheets/AI Studio |
| Python 3.8+ | https://python.org | Optional, for local runs |
| GitHub CLI | https://cli.github.com | Optional |
| Google Colab | https://colab.research.google.com | Main automation runner |

### ۲. Google Cloud Configuration (اجباری)

| سرویس | کار | لینک |
|-------|------|------|
| **Google AI Studio** | API Key Gemini 2.5 Pro | https://makersuite.google.com/app/apikey |
| **Google Drive** | folder `carpet-raw/` | https://drive.google.com |
| **Google Sheets** | 3 sheets: inventory, price, log | https://sheets.google.com |
| **Google Apps Script** | Web App deployment | https://script.google.com |

### ۳. Setup Commands

```bash
# 1. Clone this repo
git clone https://github.com/nasiricarpet54/carpet-expert-assistant.git
cd carpet-expert-assistant

# 2. Install dependencies (local runs)
pip install google-generativeai pillow requests

# 3. Set environment
export GEMINI_API_KEY="YOUR_API_KEY"
export SHEET_ID="YOUR_SHEET_ID"
```

---

## 🎯 How It Works

### Stage 1: Image Classification (Computer Vision)

```
Photo (≤20MB) → Gemini 2.5 Vision → JSON
{
  "region": "tabriz",
  "pattern_type": "lachak",
  "material": "silk",
  "age_days": 3650,
  "confidence": 0.87
}
```

### Stage 2: Price Estimation (AI Engine)

```
region + material + age + size + knots → weighted model
{'low': 2100000, 'unit': 3000000, 'high': 4050000} ← Toman
```

### Stage 3: Daily Market Sync (Automation)

- Python scraper → Bing Images + Bing Shopping
- Price data → Google Sheets (CSV, daily)
- Anomaly detection alerts via email

---

## 📊 Deployment

### Method A: Google Colab — Full Automation (Recommended)

Run `src/setup_colab.ipynb`:
1. Open https://colab.research.google.com
2. Upload `src/setup_colab.ipynb`
3. Enter `GEMINI_API_KEY` in the config cell
4. Click **Run all**

**Outputs:**
- Images → `Drive/carpet-raw/images/`
- Classification → `Drive/carpet-raw/carpets_classification.csv`

### Method B: Apps Script Web App — User Front-End

1. Open https://script.google.com → New Project
2. Copy `src/appsscript/code.gs` → create `code.gs` file
3. Copy `src/appsscript/index.html` → create `index.html` file
4. Replace `YOUR_API_KEY` and `YOUR_SHEET_ID`

5. **Deploy → New Deployment → Web App → Access: Anyone**
6. Copy the Web App URL

**Features:**
- Upload carpet photo → Gemini returns region/pattern/material
- Input manual details → returns low/mid/high price
- Auto generated PDF report

---

## 🏗️ Architecture

```
┌───────────────────────────────────────────────────┐
│                   FRONT-END (UI)                  │
│  Google Apps Script Web App ← HTML/JS/CSS form    │
│  Upload Photo | Manual Entry | Price Estimator    │
└───────────────────────┬───────────────────────────┘
                        │ HTTPS
┌───────────────────────▼───────────────────────────┐
│              Google Apps Script (Server)             │
│      Validation | Session | Audit Trail               │
└───────┬───────────────────────┬─────────────────────┘
        │                       │
┌───────▼───────┐     ┌────────▼───────┐
│   Gemini 2.5  │     │  Google Sheets │
│ Vision Model  │     │  Database      │
│  (AI Studio)  │     │  price + DB    │
└───────┬───────┘     └────────────────┘
        │
┌───────▼───────┐
│  Google Drive │
│  /carpet-raw/ │
│  + images     │
└───────────────┘
```

---

## 📈 Philosophy & Ethics

| Principle | Rule |
|-----------|------|
| **Judicial** | Never automated — always human-in-the-loop |
| **Transparency** | Every estimate has audit trail |
| **Privacy** | Images stored locally, purged after 90 days |
| **Validation** | Severity > 70% confidence required |
| **History** | Historic price from >2 sources |

---

## 🗓️ Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 0 | ✅ | Sample data collection |
| 1 | ⏳ | AI Studio integration |
| 2 | ⏳ | Sheets configuration |
| 3 | ⏳ | Web App deployment |
| 4 | ⏳ | Automated price sync |
| 5 | ⏳ | Validation & report |

---

## ©️ License

**AGPLv3** — Open source. For commercial use contact: [author@carpet-expert.com]

---

## 👤 Developed By

**Carpet Expert Assistant** — Claude Code (Opus 4)  
**For:** nasiricarpet54@gmail.com  
**Date:** 2026-11-18
