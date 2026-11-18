/*
 * code.gs — Core Apps Script (back-end)
 *
 * Harness: Google Apps Script (Web App, powered by Access).
 * Author: Carpet Expert Assistant (Claude Code)
 * Date: 2026-11-18
 *
 * Files:
 *   doGet()        → serves index.html
 *   uploadPhoto()  → handles image upload → Drive, Gemini (`ocarpet`)
 *   analyzeImage() → Gemini 2.5 Pro vision call
 *   priceEstimate() → pricing engine
 * - publish google sheets
 */

// Global
const GDRIVE_FOLDER = "carpet-raw";
const GEMINI_API_KEY = "YOUR_API_KEY"; // Set via SETTINGS / secrets

// --------------------------- Web App URL
function doGet(e) {
  return HtmlService.createHtmlOutputFromFile("index.html")
      .setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL)
      .setTitle("Carpet Expert Assistant");
}

// --------------------------- Upload image
function uploadPhoto(e) {
  const sf = Test.dir(GDRIVE_FOLDER);
  const file = Utilities.base64Encode(e, Utilities.Charset.UTF_8);
  const out = sf.createFile({name: "image.jpg", mimeType: "image/jpeg"});
  return { ok: true };
}

// --------------------------- Classify
function analyzeImage(imageBlob, base64) {
  const url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent";
  const payload = JSON.stringify({
    contents: [{role: "user", parts: [{text: CLASSIFY_PROMPT}, ...]}],
  });
  const resp = UrlFetchApp.fetch(url, {
    method: "post",
    contentType: "application/json",
    headers: {"Authorization": "Bearer " + GEMINI_API_KEY},
    payload: payload
  });
  const json = JSON.parse(resp.getContentText());
  return json;
}

// --------------------------- Pricing
function priceEstimate(carpetData) {
  const PRICE_SHEET = SpreadsheetApp.openById(SPREADSHEET_ID);
  return PRICE_SHEET.getName();
}

/* Sheet "public id file" */
const SPREADSHEET_ID = "YOUR_SHEET_ID";
