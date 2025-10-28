# Quick Font Download Links

## Indian Regional Languages - Direct Download Links

### Core Indian Languages

| Language | Script | Font Name | Download Link |
|----------|--------|-----------|---------------|
| Hindi, Marathi, Nepali, Sanskrit | Devanagari | Noto Sans Devanagari | https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari |
| Bengali, Assamese | Bengali | Noto Sans Bengali | https://fonts.google.com/noto/specimen/Noto+Sans+Bengali |
| Tamil | Tamil | Noto Sans Tamil | https://fonts.google.com/noto/specimen/Noto+Sans+Tamil |
| Telugu | Telugu | Noto Sans Telugu | https://fonts.google.com/noto/specimen/Noto+Sans+Telugu |
| Kannada | Kannada | Noto Sans Kannada | https://fonts.google.com/noto/specimen/Noto+Sans+Kannada |
| Malayalam | Malayalam | Noto Sans Malayalam | https://fonts.google.com/noto/specimen/Noto+Sans+Malayalam |
| Gujarati | Gujarati | Noto Sans Gujarati | https://fonts.google.com/noto/specimen/Noto+Sans+Gujarati |
| Punjabi | Gurmukhi | Noto Sans Gurmukhi | https://fonts.google.com/noto/specimen/Noto+Sans+Gurmukhi |
| Oriya/Odia | Oriya | Noto Sans Oriya | https://fonts.google.com/noto/specimen/Noto+Sans+Oriya |
| Sinhala | Sinhala | Noto Sans Sinhala | https://fonts.google.com/noto/specimen/Noto+Sans+Sinhala |

### Other Asian Languages

| Language | Script | Font Name | Download Link |
|----------|--------|-----------|---------------|
| Japanese | Kanji/Hiragana/Katakana | Noto Sans JP | https://fonts.google.com/noto/specimen/Noto+Sans+JP |
| Chinese (Simplified) | Han | Noto Sans SC | https://fonts.google.com/noto/specimen/Noto+Sans+SC |
| Korean | Hangul | Noto Sans KR | https://fonts.google.com/noto/specimen/Noto+Sans+KR |
| Thai | Thai | Noto Sans Thai | https://fonts.google.com/noto/specimen/Noto+Sans+Thai |
| Khmer | Khmer | Noto Sans Khmer | https://fonts.google.com/noto/specimen/Noto+Sans+Khmer |
| Lao | Lao | Noto Sans Lao | https://fonts.google.com/noto/specimen/Noto+Sans+Lao |
| Myanmar | Myanmar | Noto Sans Myanmar | https://fonts.google.com/noto/specimen/Noto+Sans+Myanmar |

### Middle Eastern Languages

| Language | Script | Font Name | Download Link |
|----------|--------|-----------|---------------|
| Arabic, Persian | Arabic | Noto Sans Arabic | https://fonts.google.com/noto/specimen/Noto+Sans+Arabic |
| Urdu | Nastaliq | Noto Nastaliq Urdu | https://fonts.google.com/noto/specimen/Noto+Nastaliq+Urdu |
| Hebrew | Hebrew | Noto Sans Hebrew | https://fonts.google.com/noto/specimen/Noto+Sans+Hebrew |

### Other Scripts

| Language | Script | Font Name | Download Link |
|----------|--------|-----------|---------------|
| Tibetan | Tibetan | Noto Sans Tibetan | https://fonts.google.com/noto/specimen/Noto+Sans+Tibetan |
| Armenian | Armenian | Noto Sans Armenian | https://fonts.google.com/noto/specimen/Noto+Sans+Armenian |
| Georgian | Georgian | Noto Sans Georgian | https://fonts.google.com/noto/specimen/Noto+Sans+Georgian |
| Ethiopic | Ethiopic | Noto Sans Ethiopic | https://fonts.google.com/noto/specimen/Noto+Sans+Ethiopic |

## Installation Priority

### High Priority (Most Common Indian Languages)
1. ✅ **Devanagari** (Hindi, Marathi) - Already installed
2. **Bengali** - 265M speakers
3. **Telugu** - 83M speakers
4. **Tamil** - 77M speakers
5. **Marathi** - 83M speakers (uses Devanagari - already works)
6. **Gujarati** - 56M speakers
7. **Kannada** - 44M speakers
8. **Malayalam** - 38M speakers
9. **Punjabi** - 33M speakers
10. **Oriya/Odia** - 38M speakers

### Medium Priority (Regional & Neighboring)
- Assamese (uses Bengali script)
- Nepali (uses Devanagari - already works)
- Sinhala (Sri Lankan)

### By Request
- East Asian (Japanese, Chinese, Korean)
- Middle Eastern (Arabic, Urdu, Persian, Hebrew)
- Southeast Asian (Thai, Khmer, Lao, Myanmar)
- Other (Tibetan, Armenian, Georgian, Ethiopic)

## Quick Download Instructions

1. Click the Google Fonts link for the desired language
2. Click **"Get font"** or **"Download family"** button
3. Extract the ZIP file
4. Copy `-Regular.ttf` file to: `d:\Projects\Client\Client_Ireland\fonts\`
5. Optionally copy `-Bold.ttf` for bold text support
6. Verify filename matches the table above
7. Restart Flask application

## Verification Command

```powershell
# List all installed fonts
Get-ChildItem "d:\Projects\Client\Client_Ireland\fonts\" | Select-Object Name, Length

# Check specific font
Test-Path "d:\Projects\Client\Client_Ireland\fonts\NotoSansBengali-Regular.ttf"
```

## Expected File Sizes

- Regular fonts: ~200-300 KB
- Bold fonts: ~210-320 KB
- CJK fonts (Japanese, Chinese, Korean): ~5-15 MB (much larger due to thousands of characters)

---

**All links lead to official Google Fonts Noto family** - guaranteed compatibility! 🎯
