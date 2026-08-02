"""
Test to verify NO markdown in scheme responses
Tests all response types to ensure clean plain text output
"""

import sys
sys.path.insert(0, '.')

from chatbot.utils.formatting import sanitize_markdown, format_scheme_answer

# Simulate markdown-heavy Gemini response
gemini_response_with_markdown = """Here are the details of the agriculture schemes:

1. **Pradhan Mantri Fasal Bima Yojana (PMFBY)**
   * **Eligibility:** Farmers (owner cultivators, tenants, sharecroppers)
   * **Benefits:** Offers affordable insurance coverage
   * **How to Apply:** Apply online at https://pmfby.gov.in

2. **Kisan Credit Card (KCC)**
   * **Eligibility:** Farmers engaged in agriculture
   * **Benefits:** Provides easy access to credit
   * **How to Apply:** Apply at scheduled banks

3. **Pradhan Mantri Krishi Sinchai Yojana (PMKSY)**
   * **Eligibility:** Farmers requiring irrigation
   * **Benefits:** Offers subsidies for micro-irrigation
   * **How to Apply:** Through state agriculture departments"""

print("=" * 80)
print("MARKDOWN REMOVAL TEST - GEMINI RESPONSE")
print("=" * 80)

print("\n📥 ORIGINAL RESPONSE (with markdown):")
print("-" * 80)
print(gemini_response_with_markdown)

print("\n\n🧹 AFTER SANITIZATION:")
print("-" * 80)
cleaned = sanitize_markdown(gemini_response_with_markdown)
print(cleaned)

print("\n\n✅ VERIFICATION:")
print("-" * 80)

# Check for any markdown symbols
markdown_symbols = ['**', '*', '•', '#', '1.', '2.', '3.', '[', ']']
found_symbols = []

for symbol in markdown_symbols:
    if symbol in cleaned:
        found_symbols.append(symbol)

if found_symbols:
    print(f"❌ FAIL: Found markdown symbols: {', '.join(found_symbols)}")
else:
    print("✅ PASS: No markdown symbols found!")

# Check that schemes are separated
lines = cleaned.split('\n')
blank_lines = sum(1 for line in lines if line.strip() == '')
print(f"\n📊 Statistics:")
print(f"   - Total lines: {len(lines)}")
print(f"   - Blank lines (separators): {blank_lines}")
print(f"   - Content lines: {len(lines) - blank_lines}")

# Check readability
print(f"\n📖 Readability Check:")
if blank_lines >= 2:
    print("   ✅ Schemes are properly separated with blank lines")
else:
    print("   ⚠️  Warning: Schemes may not be well separated")

print("\n" + "=" * 80)
if not found_symbols and blank_lines >= 2:
    print("🎉 TEST PASSED: Clean plain text with proper separation!")
else:
    print("⚠️  TEST NEEDS REVIEW")
print("=" * 80)
