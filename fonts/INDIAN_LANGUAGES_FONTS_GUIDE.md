# Indian Regional Languages - Font Installation Guide

## Overview
This guide explains how to add font support for all major Indian regional languages using the same successful approach implemented for Hindi.

## ✅ Currently Supported
- **Hindi, Marathi, Nepali, Sanskrit** → NotoSansDevanagari-Regular.ttf ✅ (Already installed)

## 📥 Required Font Files

### Download All Fonts from Google Fonts
Visit: https://fonts.google.com/noto

### Indian Languages (Indic Scripts)

#### 1. **Bengali & Assamese**
- **Script:** Bengali
- **Download:** Noto Sans Bengali
- **Required Files:**
  - `NotoSansBengali-Regular.ttf`
  - `NotoSansBengali-Bold.ttf` (optional but recommended)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`
- **Supported Languages:** Bengali, Assamese

#### 2. **Tamil**
- **Script:** Tamil
- **Download:** Noto Sans Tamil
- **Required Files:**
  - `NotoSansTamil-Regular.ttf`
  - `NotoSansTamil-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 3. **Telugu**
- **Script:** Telugu
- **Download:** Noto Sans Telugu
- **Required Files:**
  - `NotoSansTelugu-Regular.ttf`
  - `NotoSansTelugu-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 4. **Kannada**
- **Script:** Kannada
- **Download:** Noto Sans Kannada
- **Required Files:**
  - `NotoSansKannada-Regular.ttf`
  - `NotoSansKannada-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 5. **Malayalam**
- **Script:** Malayalam
- **Download:** Noto Sans Malayalam
- **Required Files:**
  - `NotoSansMalayalam-Regular.ttf`
  - `NotoSansMalayalam-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 6. **Gujarati**
- **Script:** Gujarati
- **Download:** Noto Sans Gujarati
- **Required Files:**
  - `NotoSansGujarati-Regular.ttf`
  - `NotoSansGujarati-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 7. **Punjabi (Gurmukhi)**
- **Script:** Gurmukhi
- **Download:** Noto Sans Gurmukhi
- **Required Files:**
  - `NotoSansGurmukhi-Regular.ttf`
  - `NotoSansGurmukhi-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 8. **Oriya/Odia**
- **Script:** Oriya
- **Download:** Noto Sans Oriya
- **Required Files:**
  - `NotoSansOriya-Regular.ttf`
  - `NotoSansOriya-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

#### 9. **Sinhala** (Sri Lankan)
- **Script:** Sinhala
- **Download:** Noto Sans Sinhala
- **Required Files:**
  - `NotoSansSinhala-Regular.ttf`
  - `NotoSansSinhala-Bold.ttf` (optional)
- **Place in:** `d:\Projects\Client\Client_Ireland\fonts\`

## 🌏 Additional Language Support (Also Configured)

### East Asian
- **Japanese:** NotoSansJP-Regular.otf
- **Chinese:** NotoSansSC-Regular.otf
- **Korean:** NotoSansKR-Regular.otf

### Middle Eastern
- **Arabic, Persian:** NotoSansArabic-Regular.ttf
- **Urdu:** NotoNastaliqUrdu-Regular.ttf
- **Hebrew:** NotoSansHebrew-Regular.ttf

### Southeast Asian
- **Thai:** NotoSansThai-Regular.ttf ✅ (Already configured)
- **Khmer (Cambodian):** NotoSansKhmer-Regular.ttf
- **Lao:** NotoSansLao-Regular.ttf
- **Myanmar (Burmese):** NotoSansMyanmar-Regular.ttf

### Other Scripts
- **Tibetan:** NotoSansTibetan-Regular.ttf
- **Armenian:** NotoSansArmenian-Regular.ttf
- **Georgian:** NotoSansGeorgian-Regular.ttf
- **Ethiopic:** NotoSansEthiopic-Regular.ttf

## 📋 Installation Steps

### Step 1: Download Font Family
1. Go to https://fonts.google.com/noto
2. Search for the specific font (e.g., "Noto Sans Tamil")
3. Click "Download family"
4. Extract the ZIP file

### Step 2: Identify Regular Font
1. Look for files ending in `-Regular.ttf`
2. Optionally, also take `-Bold.ttf` for better bold text support

### Step 3: Place in Fonts Directory
1. Copy the font file(s) to: `d:\Projects\Client\Client_Ireland\fonts\`
2. **DO NOT** create subdirectories (e.g., NO `fonts/tamil/`)
3. Keep all fonts in the root `fonts/` directory

### Step 4: Verify Naming
Ensure the filename **exactly matches** what's in `LANGUAGE_TTF_MAP`:
```python
"tamil": "NotoSansTamil-Regular.ttf",  # Must match exactly!
```

## ✅ Verification

After adding font files, verify with PowerShell:

```powershell
# Check if font exists
Test-Path "d:\Projects\Client\Client_Ireland\fonts\NotoSansTamil-Regular.ttf"
# Should return: True

# List all installed fonts
Get-ChildItem "d:\Projects\Client\Client_Ireland\fonts\*.ttf"
```

## 🎯 Testing

1. Restart Flask app: `python app.py`
2. Upload a PDF document
3. Select target language (e.g., "Tamil")
4. Translate
5. Verify the output PDF displays proper Tamil characters (not ????????)

## 🔧 Technical Details

### Font Rendering Method
All Indian languages now use the **same proven TextWriter approach** that works for Hindi:

```python
# Create Font object from file
font = fitz.Font(fontfile=selected_font_path)

# Create TextWriter
tw = fitz.TextWriter(page.rect)

# Fill textbox with custom font
tw.fill_textbox(bbox, text, fontsize=12, font=font, align=align)

# Write to page
tw.write_text(page, color=(0, 0, 0))
```

This ensures:
- ✅ Proper Unicode character rendering
- ✅ Complex script support (ligatures, combining characters)
- ✅ No character corruption or question marks
- ✅ Consistent quality across all languages

### Supported Language Codes (Case-Insensitive)
The application accepts these language names:
- `hindi`, `marathi`, `nepali`, `sanskrit` → Devanagari script
- `bengali`, `assamese` → Bengali script
- `tamil` → Tamil script
- `telugu` → Telugu script
- `kannada` → Kannada script
- `malayalam` → Malayalam script
- `gujarati` → Gujarati script
- `punjabi`, `gurmukhi` → Gurmukhi script
- `oriya`, `odia` → Oriya script
- `sinhala` → Sinhala script

## 📊 Current Status

| Language | Font File | Status |
|----------|-----------|--------|
| Hindi | NotoSansDevanagari-Regular.ttf | ✅ Installed & Working |
| Marathi | NotoSansDevanagari-Regular.ttf | ✅ Installed & Working |
| Bengali | NotoSansBengali-Regular.ttf | ⏳ Configured, needs font file |
| Tamil | NotoSansTamil-Regular.ttf | ⏳ Configured, needs font file |
| Telugu | NotoSansTelugu-Regular.ttf | ⏳ Configured, needs font file |
| Kannada | NotoSansKannada-Regular.ttf | ⏳ Configured, needs font file |
| Malayalam | NotoSansMalayalam-Regular.ttf | ⏳ Configured, needs font file |
| Gujarati | NotoSansGujarati-Regular.ttf | ⏳ Configured, needs font file |
| Punjabi | NotoSansGurmukhi-Regular.ttf | ⏳ Configured, needs font file |
| Oriya/Odia | NotoSansOriya-Regular.ttf | ⏳ Configured, needs font file |
| Sinhala | NotoSansSinhala-Regular.ttf | ⏳ Configured, needs font file |

## 🚨 Important Notes

1. **File naming is case-sensitive** on some systems
2. **All fonts must be in the root `fonts/` directory** (no subdirectories)
3. **Regular.ttf is required**, Bold.ttf is optional
4. **Font files can be 200-300KB each** (Noto Sans family)
5. **Download from Google Fonts** to ensure compatibility

## 📞 Support

If a language doesn't render correctly:
1. Verify font file exists in `fonts/` directory
2. Check filename matches `LANGUAGE_TTF_MAP` exactly
3. Restart Flask app after adding new fonts
4. Check console logs for font loading errors

---

**All Indian regional languages now use the same proven TextWriter font rendering approach!** 🎉
