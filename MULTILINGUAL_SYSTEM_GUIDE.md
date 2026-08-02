# Multilingual System Guide

## Overview

Your Django Government Scheme Chatbot now supports **3 languages**:
- **English (en)** - Default
- **Kannada (kn)** - ಕನ್ನಡ
- **Hindi (hi)** - हिंदी

## How It Works

### 1. Automatic Language Detection

The system automatically detects the user's language using `langdetect`:

```python
from chatbot.utils.multilingual import detect_user_language

user_language = detect_user_language("ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್")  # Returns: 'kn'
user_language = detect_user_language("PM Kisan Scheme")      # Returns: 'en'
user_language = detect_user_language("प्रधान मंत्री किसान")  # Returns: 'hi'
```

### 2. Translation Strategy

**Two-tier translation system:**

#### Tier 1: Database Translations (Preferred)
- Schemes have `title_translations` JSONField
- Pre-stored translations for scheme titles
- **Fast** and **accurate**
- Used when available

```json
{
  "title_translations": {
    "kn": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ",
    "hi": "प्रधान मंत्री किसान योजना"
  }
}
```

#### Tier 2: Gemini Translation (Fallback)
- Used when DB translation is missing
- Translates entire formatted scheme text
- Maintains field structure
- **NO markdown** in output

### 3. Response Format

All API responses now include the detected language:

```json
{
  "language": "kn",
  "response": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ ಬಗ್ಗೆ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ.",
  "schemes": ["Scheme Name: ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ\n..."],
  "match_type": "exact_match"
}
```

## Key Features

### ✅ Culturally Appropriate Greetings

**English:**
```
Hello! I'm your Government Schemes Assistant.
```

**Kannada:**
```
ನಮಸ್ಕಾರ! ನಾನು ನಿಮ್ಮ ಸರ್ಕಾರಿ ಯೋಜನೆ ಸಹಾಯಕ.
```

**Hindi:**
```
नमस्ते! मैं आपका सरकारी योजना सहायक हूँ।
```

### ✅ Localized Match Introductions

**Exact Match (Kannada):**
```
ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ ಬಗ್ಗೆ ಮಾಹಿತಿ ಇಲ್ಲಿದೆ.
```

**Fuzzy Match (Hindi):**
```
आपके लिए यह योजना मिली: प्रधान मंत्री किसान योजना
```

### ✅ Sector-Specific Messages

**English:**
```
I found 5 schemes from the Agriculture sector.
```

**Kannada:**
```
Agriculture ವಿಭಾಗದಿಂದ 5 ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ.
```

**Hindi:**
```
Agriculture क्षेत्र से 5 योजनाएँ मिलीं।
```

### ✅ No Markdown in Any Language

All text is sanitized to remove:
- Bold: `**text**` → `text`
- Italic: `*text*` → `text`
- Bullets: `• item` → `item`
- Headers: `# Title` → `Title`
- Lists: `1. item` → `item`

## API Integration

### Query Pipeline

```
User Query → detect_user_language() → 'en'/'kn'/'hi'
     ↓
Match Pipeline (exact/fuzzy/vector/sector)
     ↓
format_scheme_answer(scheme, user_language='kn')
     ↓
DB Translation Check
     ├─ Has Translation → Use DB
     └─ No Translation → Gemini Translate
     ↓
sanitize_markdown() → Remove formatting
     ↓
JSON Response with 'language' field
```

### Example API Call

```python
# POST /api/chatbot/smart-query/
{
  "query": "ಕೃಷಿ ಯೋಜನೆಗಳು"
}

# Response
{
  "language": "kn",
  "response": "Agriculture ವಿಭಾಗದಿಂದ 5 ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ.",
  "schemes": [
    "Scheme Name: ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ\nSector: Agriculture\n...",
    ...
  ],
  "match_type": "sector_match"
}
```

## Utility Functions

### `detect_user_language(text)`

Detects language from input text.

```python
from chatbot.utils.multilingual import detect_user_language

lang = detect_user_language("ನಮಸ್ಕಾರ")  # 'kn'
```

### `translate_with_gemini(text, target_language)`

Translates English text to Kannada or Hindi.

```python
from chatbot.utils.multilingual import translate_with_gemini

kannada = translate_with_gemini("Hello World", 'kn')
hindi = translate_with_gemini("Hello World", 'hi')
```

### `get_friendly_greeting(language)`

Returns culturally appropriate greeting.

```python
from chatbot.utils.multilingual import get_friendly_greeting

greeting = get_friendly_greeting('kn')  # "ನಮಸ್ಕಾರ!..."
```

### `get_match_intro(language, match_type, scheme_title, count)`

Returns localized match introduction.

```python
from chatbot.utils.multilingual import get_match_intro

intro = get_match_intro('hi', 'exact_match', 'PM Kisan Scheme')
# "आपके लिए यह योजना मिली: PM Kisan Scheme"
```

### `get_sector_intro(language, sector, count)`

Returns sector-specific introduction.

```python
from chatbot.utils.multilingual import get_sector_intro

intro = get_sector_intro('kn', 'Agriculture', 5)
# "Agriculture ವಿಭಾಗದಿಂದ 5 ಯೋಜನೆಗಳು ಸಿಕ್ಕಿವೆ."
```

### `get_no_scheme_message(language, query)`

Returns "no scheme found" message.

```python
from chatbot.utils.multilingual import get_no_scheme_message

msg = get_no_scheme_message('hi', 'random query')
# "'random query' से मेल खाने वाली कोई योजना नहीं मिली..."
```

### `translate_scheme_if_needed(scheme_text, user_language, scheme_has_translation)`

Conditionally translates scheme text.

```python
from chatbot.utils.multilingual import translate_scheme_if_needed

# Only translates if user_language is 'kn'/'hi' AND no DB translation
translated = translate_scheme_if_needed(
    scheme_text="Scheme Name: PM Kisan...",
    user_language='kn',
    scheme_has_translation=False  # No DB translation
)
```

## Testing

### Run Multilingual Tests

```bash
python test_multilingual_system.py
```

**Test Coverage:**
- ✅ Language detection (English, Kannada, Hindi)
- ✅ Friendly greetings (3 languages)
- ✅ Sector introductions (3 languages)
- ✅ Match introductions (all match types)
- ✅ No scheme messages (3 languages)
- ✅ Gemini translation (optional, requires API)

### Manual Testing

**Test English:**
```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "pm kisan scheme"}'
```

**Test Kannada:**
```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ"}'
```

**Test Hindi:**
```bash
curl -X POST http://localhost:8000/api/chatbot/smart-query/ \
  -H "Content-Type: application/json" \
  -d '{"query": "प्रधान मंत्री किसान योजना"}'
```

## Database Setup

### Add Translations to Schemes

```python
from chatbot.models import GovernmentScheme

scheme = GovernmentScheme.objects.get(title="PM-Kisan Scheme")
scheme.title_translations = {
    'kn': 'ಪ್ರಧಾನ ಮಂತ್ರಿ ಕಿಸಾನ್ ಯೋಜನೆ',
    'hi': 'प्रधान मंत्री किसान योजना'
}
scheme.description_translations = {
    'kn': 'ರೈತರಿಗೆ ನೇರ ಆದಾಯ ಬೆಂಬಲ',
    'hi': 'किसानों के लिए प्रत्यक्ष आय सहायता'
}
scheme.save()
```

### Bulk Update Script

```python
# Example: Add Kannada translations for all schemes
from chatbot.models import GovernmentScheme

schemes = GovernmentScheme.objects.all()
for scheme in schemes:
    if not scheme.title_translations:
        scheme.title_translations = {}
    
    # Add Kannada translation (use translation API or manual entry)
    scheme.title_translations['kn'] = translate_to_kannada(scheme.title)
    scheme.save()
```

## Performance Considerations

### Database Translations (Fast)
- **Instant** - No API call
- **Free** - No usage cost
- **Accurate** - Pre-verified translations
- **Recommended** for frequently accessed schemes

### Gemini Translations (Slower)
- ~1-2 seconds per translation
- Uses API quota
- Good for dynamic content
- Automatic fallback when DB translation missing

## Configuration

### Environment Variables

```env
# Gemini API Key (required for translation fallback)
GEMINI_API_KEY=your-api-key-here
```

### Language Detection Settings

```python
# chatbot/utils/multilingual.py

# Adjust detection sensitivity
DetectorFactory.seed = 0  # Consistent results

# Add more languages (if needed)
SUPPORTED_LANGUAGES = ['en', 'kn', 'hi', 'ta', 'te']
```

## Troubleshooting

### Issue: Wrong Language Detected

**Cause:** Query too short or mixed languages

**Solution:**
- Use longer, more descriptive queries
- Default to English for ambiguous cases
- Check `DetectorFactory.seed` setting

### Issue: Translation Not Working

**Cause:** Gemini API key missing or invalid

**Solution:**
- Check `GEMINI_API_KEY` in environment
- Verify API key has sufficient quota
- Check error logs for API response

### Issue: Markdown in Translated Text

**Cause:** Gemini adds markdown formatting

**Solution:**
- `sanitize_markdown()` is automatically applied
- Check translation system prompt in `multilingual.py`
- Verify prompt includes "NO markdown" instruction

## Files Modified

### New Files
- `chatbot/utils/multilingual.py` - Complete multilingual utilities
- `test_multilingual_system.py` - Comprehensive test suite
- `MULTILINGUAL_SYSTEM_GUIDE.md` - This guide

### Modified Files
- `requirements.txt` - Added `langdetect`
- `chatbot/utils/formatting.py` - Added `user_language` parameter to `format_scheme_answer()`
- `chatbot/views.py` - Updated all response types with multilingual support

## Next Steps

1. **Add Database Translations**
   - Create script to bulk-translate scheme titles
   - Use professional translation service for accuracy
   - Store in `title_translations` and `description_translations` fields

2. **Frontend Integration**
   - Use `language` field from API response
   - Apply appropriate text direction (LTR for all 3 languages)
   - Display in correct font (Noto Sans Kannada, Noto Sans Devanagari)

3. **Add More Languages** (Optional)
   - Tamil (ta)
   - Telugu (te)
   - Bengali (bn)
   - Gujarati (gu)
   - Marathi (mr)
   - Punjabi (pa)

4. **Performance Optimization**
   - Cache Gemini translations in Redis
   - Pre-translate popular schemes
   - Use batch translation for multiple schemes

## Summary

✅ **Complete multilingual system implemented**
✅ **3 languages supported: English, Kannada, Hindi**
✅ **Automatic language detection**
✅ **Two-tier translation: DB + Gemini fallback**
✅ **NO markdown in any language**
✅ **Culturally appropriate greetings**
✅ **All 6 test suites passing**

Your chatbot is now production-ready for multilingual users! 🎉
