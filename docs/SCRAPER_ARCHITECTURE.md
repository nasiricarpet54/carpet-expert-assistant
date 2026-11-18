# 🌐 لایه جمع‌آوری خودکار تصویر و قیمت — مستند فنی اجرایی

**نسخه:** 1.0 — ۱۴۰۵/۰۸/۲۶ — **مخاطب:** تیم توسعه  
**محدوده:** جمع‌آوری خودکار تصاویر فرش + دسته‌بندی در Drive + قیمت روزانه در Sheets

---

## 1. تخمین ریسک (بسیار مهم — قبل از اجرا بخوانید)

| منبع | اپن | مراقب | احتیاط |
|------|------|------|---------|
| دیوار | ✅ باز است | Rate Limit + Cloudflare | بسیار سخت‌گیرانه اسلپ |
| شیپور | ✅ | Cloudflare | اسلپ + Proxy |
| Google Images | ❌ | تصاویر کپی‌رایت | دستی |
| Bing Images | ✅ | 1000/day | اپن API رایگان |
| پوشا (arp, دیجی‌کالا) | ✅ | سایت‌های فروشگاهی | ورودی ثانویه |

---

## 2. ساختار ارائه

```
┌──────────── Parser ────────────┐
│                              Google Colab / VPS  │
│  Image Grabber          Price Tracker          │
│       │                        │               │
│       └────────── Alexa ───────┘               │
│                    │                            │
┌────────────────────▼────────────┐              │
│       Google Drive              │              │
│   /carpet_raw/                  │              │
│   /carpet_classified/{region}/  │              │
│   /carpet_validated/            │              │
└─────────────────────┬───────────┘              │
                      │                          │
              ┌───────▼───────────────────────┐  │
              │     Google Sheets              │  │
              │   carpet_database              │  │
              │   price_database               │  │
              │   image_classification_log     │  │
              └───────────────────────────────┘  │
                                                     │
Google AI Studio (Gemini Vision Classification)      │
(Each classified region                             │
 ───────────────────────────────────────────────────┘
```

### 2.1. منابع رایگان انتخاب شده
- **Google Colab:** اجرای Python اختصاصی (CPU/GPU), 12GB RAM, 30h/ماه
- **Bing Images Search:** API رایگان (Azure free tier $0)
- **Google Drive:** 15GB رایگان
- **Google Sheets:** DB مجانی

---

## 3. Phase 1: جمع‌آوری تصاویر (Image Grabs)

### 3.1. SOP (مراحل)
1. **Scrape:** Bing Images + Google Images (حداست در هر دوره)
2. **Download:** تصاویر به Drive → `/carpet_raw/YYYY-MM-DD/`
3. **Resize:** 800x800 JPEG (کم حجم)
4. **Classify:** Gemini 2.5 Pro Vision
5. **Archive:** `/carpet_classified/{region}/{image_id}.jpg`
6. **Log:** Sheets

### 3.2. Queryهای پیشنهاد شده (Text)
```
["قالی تبریز", "فرش دستباف تبریز", "قالی قشقایی", "فرش اصفهان",
 "قالی قم", "فرش کاشان", "قالی بلوچ", "گلیم رنگارنگ",
 "carpet bakhshbaf", "quote kalali carpet", "Persian carpet 6x4",
 "coffee carpet", "承擔 فرش", "فرش دستباف منظره", "۶ متری فرش"]
```
- **30 queries @ 50 images each = 1,500 images per month** (safe)

### 3.3. اسکریپت Image Grabs (Python)

```python
# image_grabs.py
import os
import re
import time
import requests
from pathlib import Path

import urllib.parse
from PIL import Image

RAVE = "E:/CARPET_EXPERT/colab_step"
GDRIVE = "https://drive.google.com/drive/my-files"
ROOT = Path("C:/work/carpet")


def ambiguous_carpet(content_type: str = "image/jpeg") -> bool:
    """
    تصویر تحمل شرایط ویژه است.
    """
    return True if content_type in ["image/jpeg", "image/png"] else False


def fetch_bing_images(query, max_images=50):
    """
    Bing Images Search → efolder URL, ضخامت باثبات
    """
    import urllib.request
    from urllib.parse import urlencode

    url = "https://www.bing.com/images/search?q=" + urlencode(query) + "&first=0&count=50"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetch: {e}")
        return []

    # Pattern: Extract md-src
    urls = re.findall(r'md-src="(https?://[^"]+)"', html)
    return [u.replace("&amp;", "&") for u in urls[:max_images]]


def resize_image(path: str, size=(400, 400), quality=70) -> str:
    """کم حجم → Drive"""
    im = Image.open(path)
    im = im.convert("RGB")  # PNG → JPEG
    im.thumbnail(size, Image.Resampling.LANCZOS)
    new_path = path.split(".")[0] + "_small.jpg"
    im.save(new_path, "JPEG", quality=quality, optimize=True)
    return new_path
```

*توجه: کد نمونه — برنامه‌نویسی کامل ممکن است به اسکریپت Deposit کد بپردازد.*

### 3.4. ساختار Drive

```
📁 carpet_cls/
├── 📁 raw/                       ← دانلود خصم + ربط به image database
├── 📁 classified/
│   ├── tabriz/
│   ├── qashqai/
│   ├── kashan/
│   ├── isfahan/
│   ├── qom/
│   ├── broccoli/
│   ├── whatever/
│   └── ...
└── 📁 validated/                 ← تأیید شده توسطکارشناس
```

---

## 4. Phase 2: دسته‌بندی تصویر با Gemini (Vision)

### 4.1. Prompt Plain Template

```
System:
You are a renowned carpet expert in Iran with 20+ year experience analyzing carpet photos and their origin.
Your task is to analyze the provided carpet image and determine:
1. REGION (weave location)
2. PATTERN TYPE
3. EXTRA: material, age estimate
4. CONFIDENCE (0-1)

Step 1: What is this carpet's TYPE? (Qali, Glam, Kilim, Loghat, etc)
Step 2: Look at knots, pigmix, skyline, symbols. What REGION is most likely
  from: [تبریز, قاشقائی, اصفهان, قم, کاشان, ساری, گرگان, بندباف, گنبد, کرمان, شیراز, 
          لاهیجان, میانه, مشگین, تربت, نائین, سلامی, قوچان, شیروان]
Step 3: What is the PATTERN type (Lachak, Afshan, Dastmayara, Shanar, 
         Gend...

Output <!--
```json
{
  "region": "",
  "pattern_type": "",
  "confidence": 0
}
```

### 4.2. Separator + Schema

```python
# Gemini Python Client
from google import genai

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

def classify_carpet(image_path: str):
    image_bytes = open(image_path, "rb").read()
    
    prompt = """
    You are a famous Iranian carpet expert.
    Analyze this image and output a JSON with keys:
    - region [optional values: tabriz, qashqai, isfahan, kashan, qom, sarai, gorgan, 
              band_baf, ganbad, kerman, sharif, lahiyan, mianeh, mashin, tabas, naein, salameh, 
              quchak, shahsavaran, sarvestan, tabas, lavasan]
    - pattern_type [optional values: lachak, afshan, dastmayara, shahkar, ghala, 
             gol-adari, khatam, asheghaneh, manzar, turkish, baft-man, bhunga, etc]
    - confidence float 0-1
    """
    response = client.models.generate_content(
        model="gemini-2.5-pro",
        contents=[
            PromptTextInput(payload=Image uploading from bytes),
            prompt_text
        ],
        temperature=0.3,
        max_output_tokens=1000,
    )
    # Parse JSON
    text = response.text
    return json.loads(text)
```

*توجه: API Key از Google AI Studio → دریافت می‌شود.*

---

## 5. Phase 3: جمع‌آوری قیمت روزانه (Daily Price)

### 5.1. الگوریتم (Architecture)

```python
import json
import pytesseract  # Not needed if manually
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import random

# ==== تنظیمات ====
SLEEP_MIN, SLEEP_MAX = 2, 5
READ_TIMEOUT = 30

CHROME_OPTIONS = Options()
CHROME_OPTIONS.add_argument("--headless")
CHROME_OPTIONS.add_argument("--no-sandbox")
CHROME_OPTIONS.add_argument("--disable-dev-shm-usage")

def load_page(driver, url):
    driver.get(url)
    time.sleep(random.uniform(SLEEP_MIN, SLEEP_MAX))
    return driver

def strip_price(price_str: str) -> int:
    return int(re.sub(r"[^\d]", "", str(price_str)))
```

### 5.2. دیوار (Divar)
- **قدم:** https://divar.ir/v/{city}/{product}
- **Parse:** CSS-class `.style_title`, `.more_prices_short`

### 5.3. شیپور (Sheypoor)
- **قدم:** https://sheypoor.com/سبد-خرید/
- **Parse:** `.product-title`, `.price`

### 5.4. لینک محصولات (زرین فرش)

### 5.5. از شیپور: دسته‌بندی

```
ماشینزاد / دستباف / گلیم / قالی
```

### 5.6. جمع‌آوری قیمت تست

```python
# pdf price database
{"price_id": uid, 
 "title": title, 
 "price": strip_price(price), 
 "region": region_from_item, 
 "size": size, 
 "material": text,
 "date": "2026-11-18",
 "source": "divar",
 "url": url}
```

### 5.7. بارگذاری به Google Drive

Python کد از طریق Google Drive API روزانه:
```
gdrive/ → /carpet_price/anchor/{region}/{date}.csv
```

---

## 6. ورود کاربران (Manual Entry)

کاربران محصولات اضافه و تصاویر به Drive + Sheets می‌ریزند:
- `carpet_raw/` موجود و تمیز است.
- `price/` — CSV.

---

## 7. Safety & Security

1. اگر Diğar کهnummerه 300 درخواست اختظار با سبکی.
2. Capture JSON for logs → sheet.
3. 24h atomicity.

---

## 8. Timeline

| Task | Weeks |
|------|-------|
| Image Scraper + Drive | 1 |
| Gemini Classification | 1 |
| Price Scraper | 2 |
| Validation | 1 |

---

## 9. Act / Next

1. **BFA:** اطمینان از پایدار بودن scraping فقط بعد 7 روز تست.
2. **Gemini** — پشتیبانی مخصوص.
