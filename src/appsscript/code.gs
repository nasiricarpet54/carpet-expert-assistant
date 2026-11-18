/**
 * Carpet Expert Assistant — Apps Script Backend (بازنویسی‌شده)
 */

// ===== تنظیمات — این دو خط را جایگزین کنید =====
const GEMINI_API_KEY  = "YOUR_API_KEY";
const SPREADSHEET_ID  = "YOUR_SHEET_ID";
// ================================================

const DRIVE_FOLDER_NAME = "carpet-raw";
const GEMINI_MODEL      = "gemini-2.0-flash";

// ---------- Web App Entry
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile("index")
    .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
    .setTitle("Carpet Expert Assistant");
}

// ---------- Helpers
function getOrCreateFolder_(name) {
  const it = DriveApp.getFoldersByName(name);
  if (it.hasNext()) return it.next();
  return DriveApp.createFolder(name);
}

function getSheet_(name, headers) {
  const ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  let sh = ss.getSheetByName(name);
  if (!sh) {
    sh = ss.insertSheet(name);
    if (headers) sh.appendRow(headers);
  } else if (sh.getLastRow() === 0 && headers) {
    sh.appendRow(headers);
  }
  return sh;
}

function seedPriceDatabaseIfEmpty_() {
  const sh = getSheet_("price_database", [
    "region", "material", "base_price_per_m2",
    "knots_multiplier", "age_depreciation_per_year"
  ]);
  if (sh.getLastRow() < 2) {
    const seed = [
      ["تبریز",  "wool", 15000000, 1.20, 0.02],
      ["کاشان",  "silk", 80000000, 1.50, 0.01],
      ["اصفهان", "wool", 20000000, 1.30, 0.02],
      ["نایین",  "wool", 18000000, 1.25, 0.02],
      ["قم",     "silk", 70000000, 1.40, 0.01],
      ["مشهد",   "wool", 12000000, 1.10, 0.02]
    ];
    seed.forEach(r => sh.appendRow(r));
  }
}

// ---------- تحلیل تصویر با Gemini
function analyzeImage(file, base64) {
  try {
    const clean = String(base64).replace(/^data:image\/[a-zA-Z]+;base64,/, "");

    // ذخیره در Drive
    const folder = getOrCreateFolder_(DRIVE_FOLDER_NAME);
    const blob   = Utilities.newBlob(
      Utilities.base64Decode(clean),
      "image/jpeg",
      "carpet_" + Date.now() + ".jpg"
    );
    const driveFile = folder.createFile(blob);
    try {
      driveFile.setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
    } catch (e) { /* ممکن است policy سازمان اجازه ندهد */ }
    const fileUrl = driveFile.getUrl();

    // فراخوانی Gemini
    const prompt = `شما یک کارشناس فرش ایرانی هستید. این تصویر فرش را تحلیل کن.
پاسخ را دقیقاً به صورت JSON با این ساختار برگردان (بدون متن اضافه):
{
  "region": "منطقه بافت (تبریز، کاشان، اصفهان، نایین، قم، مشهد یا نامشخص)",
  "pattern_type": "نوع نقشه (لچک‌ترنج، افشان، خشتی، گلیم، ...)",
  "material": "wool یا silk یا cotton یا other",
  "confidence": عدد بین 0 و 1,
  "condition": "توضیح یک‌خطی وضعیت ظاهری"
}`;

    const payload = {
      contents: [{
        parts: [
          { text: prompt },
          { inline_data: { mime_type: "image/jpeg", data: clean } }
        ]
      }],
      generationConfig: {
        temperature: 0.2,
        responseMimeType: "application/json"
      }
    };

    const url = "https://generativelanguage.googleapis.com/v1beta/models/" +
                GEMINI_MODEL + ":generateContent?key=" +
                encodeURIComponent(GEMINI_API_KEY);

    const resp = UrlFetchApp.fetch(url, {
      method: "post",
      contentType: "application/json",
      payload: JSON.stringify(payload),
      muteHttpExceptions: true
    });

    const status = resp.getResponseCode();
    const text   = resp.getContentText();
    if (status !== 200) {
      throw new Error("Gemini HTTP " + status + " → " + text.substring(0, 300));
    }

    const json = JSON.parse(text);
    const outText = json.candidates &&
      json.candidates[0] &&
      json.candidates[0].content &&
      json.candidates[0].content.parts &&
      json.candidates[0].content.parts[0] &&
      json.candidates[0].content.parts[0].text;
    if (!outText) throw new Error("پاسخ Gemini خالی بود");

    // parse کردن JSON
    let parsed;
    try {
      const cleaned = outText.replace(/^```json\s*/i, "").replace(/```\s*$/, "").trim();
      parsed = JSON.parse(cleaned);
    } catch (e) {
      parsed = {
        region: "نامشخص", pattern_type: "نامشخص",
        material: "other", confidence: 0,
        condition: outText.substring(0, 200)
      };
    }

    // لاگ در شیت
    const logSheet = getSheet_("image_classification_log", [
      "timestamp", "file_url", "region", "pattern_type",
      "material", "confidence", "condition", "raw_json"
    ]);
    logSheet.appendRow([
      new Date(), fileUrl,
      parsed.region || "", parsed.pattern_type || "",
      parsed.material || "", Number(parsed.confidence) || 0,
      parsed.condition || "", JSON.stringify(parsed)
    ]);

    // پاسخ (تصویر به صورت data URL تا در HTML مستقیم نمایش داده شود)
    return {
      region:       parsed.region       || "نامشخص",
      pattern_type: parsed.pattern_type || "نامشخص",
      material:     parsed.material     || "other",
      confidence:   Number(parsed.confidence) || 0,
      condition:    parsed.condition    || "",
      image:        "data:image/jpeg;base64," + clean
    };
  } catch (err) {
    throw new Error("خطا در تحلیل تصویر: " + err.message);
  }
}

// ---------- تخمین قیمت
function priceEstimate(carpet) {
  try {
    seedPriceDatabaseIfEmpty_();
    const sh   = getSheet_("price_database", null);
    const rows = sh.getDataRange().getValues();
    if (rows.length < 2) throw new Error("داده قیمت موجود نیست");

    const data     = rows.slice(1).filter(r => r[0] !== "" || r[1] !== "");
    const region   = String(carpet.region   || "").trim();
    const material = String(carpet.material || "wool").trim();
    const sizeM    = Number(carpet.sizeM)   || 0;
    const knots    = Number(carpet.knots)   || 0;
    const ageYears = Number(carpet.ageYears)|| 0;

    let match = data.find(r => String(r[0]).trim() === region && String(r[1]).trim() === material);
    if (!match) match = data.find(r => String(r[1]).trim() === material);
    if (!match) match = data[0];

    const basePricePerM2 = Number(match[2]) || 10000000;
    const knotMult       = Number(match[3]) || 1.0;
    const ageDep         = Number(match[4]) || 0.02;

    const knotFactor = knots > 0 ? Math.min(1.8, 0.7 + (knots / 1000) * 0.3) : 1.0;
    const ageFactor  = Math.max(0.2, 1 - ageYears * ageDep);

    const unit  = Math.round(basePricePerM2 * knotMult * knotFactor * ageFactor);
    const total = unit * Math.max(1, sizeM);

    const fmt = (n) => Math.round(n).toLocaleString("fa-IR");
    return {
      unit: fmt(unit),
      low:  fmt(total * 0.8),
      high: fmt(total * 1.2)
    };
  } catch (err) {
    throw new Error("خطا در تخمین قیمت: " + err.message);
  }
}

// ---------- تست دستی (اختیاری)
function _testSetup() {
  Logger.log("Spreadsheet: " + SpreadsheetApp.openById(SPREADSHEET_ID).getName());
  Logger.log("Folder: "      + getOrCreateFolder_(DRIVE_FOLDER_NAME).getName());
  seedPriceDatabaseIfEmpty_();
  Logger.log("price_database seeded ✅");
}