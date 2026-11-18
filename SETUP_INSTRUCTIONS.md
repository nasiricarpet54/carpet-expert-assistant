# 🚀 راه‌اندازی و استقرار پروژه

**تاریخ:** ۲۰26-11-18  
**کاربر:** nasiricarpet54

---

## 📦 وضعیت فعلی

✅ پروژه روی `E:\CARPET_EXPERT` آماده است — گیت init شده  
✅ `remote: origin` = `https://github.com/nasiricarpet54/carpet-expert-assistant.git`  
❌ ریپو **روی GitHub ساخته نشده**  
❌ احراز هویت **لاجین نشده** (GitHub CLI نیاز به مرورگر دارد)

---

## مرحله ۱: ساخت ریپو روی GitHub

از خطاهای اورین:

```
https://github.com/new
نام: carpet-expert-assistant
Visibility:private (پیشنهاد من)
✅ Initialize this repository with a README
```

**الان این کار را انجام دهید** — سپس به من اطلاع دهید تا `git push` بدهم.

---

## مرحله ۲: احراز هویت ( ama آپشن )

**گزینه A — ساده:**  
```bash
# در Terminal:
gh auth login
```
 مرورگر باز می‌شود. CLI را OK کنید.

**گزینه B — PAT (بدون مرورگر):**  
ی جایی: https://github.com/settings/tokens  
Create → Public (repo) → کپی کنید  
```bash
export GH_TOKEN=ghp_xxxx...
```

---

## مرحله ۳: آپلود کدها

بعد از ساخت ریپو:
```bash
cd E:\CARPET_EXPERT
git push --set-upstream origin master
```

---

## مرحله ۴: تنظیمات Google Cloud (برای GitHub application)

1. **Google AI Studio:** https://makersuite.google.com → API Key_new
2. **Google Sheets:** یک Sheet بسازید
3. **Google Drive:** پوشه `carpet-raw` بسازید

---

## مرحله ۵: انتشار (Deploy)

- Apps Script: Web App → deploy
- Python scripts: Google Colab (monthly)

---
