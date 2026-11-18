# 🌐 لایه جمع‌آوری خودکار داده (Web Scraping Layer)

**نسخه:** 1.1 — ۱۴۰۵/۰۸/۲۶ (2026-11-18)  
**موضوع:** جمع‌آوری خودکار تصاویر فرش + قیمت‌گذاری روزانه  
**پلتفرم:** Google Cloud (رایگان)

---

## 1. هشدارهای کلیدی (قبل از اجرا)

### ⚠️ محدودیت‌های قانونی و فنی
| مسئله | وضعیت | راه‌حل |
|-------|-------|--------|
| قوانین سایت‌های ایرانی (دیوار/شیپور) | ممنوعیت scraping در Rules | استفاده با رعایت `robots.txt` + Rate Limiting سخت‌گیرانه |
| Image Copyright | نمی‌توان تصاویر خریداران را "مال خود" کرد | فقط استفاده داخل دیتابیس برای آموزش (Fair Use) |
| IP Ban / Cloudflare | بلاک شدن IP بعد از تعدادی درخواست | Rotate proxies / Sleep بین درخواست‌ها |
| محدودیت Google Drive | حجم 15GB رایگان | فشرده‌سازی تصاویر + پاک‌سازی منظم |
| محدودیت GitHub Cache | برای Herkule / GitHub Actions | Google Cloud Functions |

### ✅ راه‌حل نهایی: اوب دیجیتال (Hybrid)
- **داده تلایه (Images):** عمده از scraping + ورود دستی (تکمیل‌کننده)
- **قیمت:** ورودی CSV + Auto-sync هفتگی + ورود دستی روزانه
- **اعتبارسنجی:** ۲ لایه — هوش مصنوعی + کاربر

---

## 2. معماری جمع‌آوری خودکار

```
┌───────────────────────────────────────────────────────────────┐
│  احمد (Scheduler)                                             │
│  Google Cloud Functions (Schedule) — روزانه                  │
└───────┬───────────────────────┬───────────────────────────────┘
        │                       │
┌───────▼───────┐     ┌────────▼──────────────┐
│  Image Finder  │     │  Price Tracker        │
│  (Google 2.5   │     │  (Scrapers)           │
│  Vision + LLM) │     │                      │
│               │     │  Google Colab ⭐       │
└───────┬───────┘     └────────┬──────────────┘
        │                       │
┌───────▼───────┐     ┌────────▼──────────────┐
│  Drive        │     │  Google Sheets        │
│  - Carpet     │     │  - Region/Type prices │
│    /Raw/     │     │  - Date-stamped       │
│  - Carpet     │     │  - Validate           │
│    /Category/│     │                       │
└───────────────┘     └───────────────────────┘
```

---

## 3. لایه تصویر (Image Collection & Classification)

### 3.1. منابع تصویر (چه چیزهایی جمع می‌شود)
| منبع | نوع | مثال |
|--------|------|------|
| Google Images / Search | عکس‌های ایرانی | 반영ا، دیوار، شیپور |
| Pinterest | عکس‌های قالی محلی | جالینوس، لاله |
| Instagram (عکس) | عکس‌های آتلیه | @carpet_ir |
| Bing Images (غیرفعال) | عکس‌های خارجی | - |
| سایت‌های تخصصی فرش | عکس‌های مرجع | zarin-carpet.ir |

### 3.2. پرس‌وجو (Query) ساده‌ترین
- `قالی تبریز`
- `فرش ۶۰۰ متری`
- `قالی دستباف لچک`
- `فرش اصفهان قدیمی`
- `carpet warp Persian`
- `قالین قاشقائی`

### 3.3. فرآیند جمع‌آوری (Workflow)
1. **جمع‌آوری در لحظه:** تصاویر را از URL بخوان → دانلود = تصویر
2. ** فشرده:** Resize به 800x800 → فشرده به JPEG کیفیت 70
3. **ตะبین:** Gemini 2.5 Pro Vision classify = منطقه
4. **ذخیره:** Drive `/carpet_raw/` + `/carpet_classified/{region}/{id}.jpg`
5. **لاگ:** Sheet برای هر تصویر

### 3.4. ساختار Google Drive
```
📁 Carpet-Expert/
├── 📁 raw/                    # تصاویر خام (تنظیم‌نشده)
│   ├── 2026-11-18/
│   │   ├── img_001.jpg (https://...)
│   │   └── ...
├── 📁 classified/
│   ├── tabriz/
│   ├── qashqai/
│   ├── kirman/
│   ├── isfahan/
│   └── ...
└── 📁 validated/              # تأیید‌شده توسط کارشناس
    └── ...
```

### 3.5. ساختار Google Sheet (image_database)
| کمه | نوع |
|------|-----|
| id | auto |
| url | text |
| local_path | text |
| region_detected | text |
| pattern_detected | text |
| confidence | number |
| date_scraped | date |
| status | text (raw/classified/validated) |
| original_drive_id | text |
| notes | text |

### 3.6. برنامه (Python + Selenium) — مکان‌شده در Colab
```python
# لازم است: عکس‌ها از طریق Google Images API
# (بدون API) → Bing Search (رایگان تا 1000/day)
```

### 3.7. روش Alternativos (رایگان‌ترین)
- **Google Collab + BeautifulSoup** ← پیشنهادی
- **GitHub Actions (رایگان)** ← محدود به 20h/month
- **Google Cloud Functions** ← $300 رایگان ماهانه

---

## 4. لایه قیمت (Price Collection)

### 4.1. منابع قیمت
| منبع | URL | روش دسترسی |
|------|-----|-----------|
| دیوار | divar.ir | API رسمی ندارد → Scraping (محدود) |
| شیپور | sheypoor.com | API رسمی ندارد → Scraping (محدود) |
| ترب | torob.com | API رسمی ندارد → Scraping (محدود) |
| باسلام | basalam.com | Open Marketplace — OK |
| Amazon | amazon.com | زائد (قیمت ارزی) |
| eBay | ebay.com | زائد (قیمت ارزی) |
| سایت‌های تخصصی فرش | - | - |

### 4.2. فرآیند جمع‌آوری قیمت
1. **ربط‌گیری:** Daily (هر 24 ساعت) → آدرس‌های هدف
2. **اسکراپ:** اطلاعات محصولات (عکس، قیمت، مشخصات)
3. **تمیزکاری:** حذف Duplicate، Validation
4. **انتشار:** اضافه کردن به Google Sheets

### 4.3. ساختار Google Sheet (price_database)
| کمه | نوع |
|------|-----|
| price_id | auto |
| carpet_id | text |
| title | text |
| price | number (تومان) |
| region | text |
| size | text |
| material | text |
| condition | text |
| source | text (divar/sheypoor/others) |
| url | text |
| scraped_at | date |
| confidence | number |

### 4.4. ریسک‌های Scraping
| ریسک | راه‌حل |
|------|--------|
| IP Ban | Sleep 2-5 ثانیه بین هر درخواست + Proxy Rotate |
| Cloudflare | Captcha چکر → Skip آن سبک |
| تغییر DOM | Monitor + Alert + Manuel Fix |
| قیمت قدیمی | Allocation by date |

---

## 5. طراحی Cron (زمان‌بندی)

### 5.1. Google Apps Script — Scheduler
```javascript
function dailyPriceUpdate() {
  // هر 24 ساعت
}
function dailyImageCollect() {
  // هر ۲۴ ساعت (500-1000 تصویر)
}
```

### 5.2. Google Cloud Functions — Cron Job
- **Cost:** $0 (Free Tier)
- **Trigger:** Time-based (این گاهی به دست می‌آید)

### 5.3. GitHub Actions — Free
- دندان‌شناسی **متوسط** ماهانه 500 دقیقه

### 5.4. استفاده من: Google Cloud Scheduler + Pub/Sub → Cloud Functions

---

## 6. امنیت و اخلاق

- **нется** محتوای IP و کاربران
- **حدود ۲۴ دقیقه** = Budget حدود $300/ماهی
- **Bearer Token:** Safe

---

## 7. قدم‌های اجرایی

### очередь 1: جمع‌آوری عکس (۱ هفته)
- [ ] نصب Google Colab + Selenium
- [ ] اسکریپت اسکراپ عکس از Bing imagens
- [ ] ساختمان Drive + ساختار پوشه

### очередь 2: تشخیص تصویر (۲ هفته)
- [ ] Prompt Engineering با Gemini Vision
- [ ] دسته‌بندی و ανuggling

### очередь 3: جمع‌آوری قیمت (۲ هفته)
- [ ] اسکریپت دیوار/شیپور (با Sleep)
- [ ] تمیزکاری + درج در Sheets

### очередь 4: اتصال (۱ هفته)
- [ ] Apps Script UI
- [ ] تمیزکاری

---

## 8. Limitations و حقایق

1. **هیچ سیستم رایگان** ۱۰۰٪ قابل اعتماد نیست
2. **قیمت دیوار/شیپور** اغلب بایگانی شده است
3. **تصاویر** نیاز به دستی اوج دارد
4. **Google Drive** 15GB → پاک‌سازی منظم

---

## 9. پیشنهاد جایگزین (اگر Scraping شکست خورد)

- **ورودی دستی کاربران** → صورتحساب + پشتیبانی
- **مجری داخلی هوشمند** (Language Model) ← پیشنهاد: $0، تمام تصاویر + قیمت با انتقاد
