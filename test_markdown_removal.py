"""
Quick test to verify markdown removal works correctly
"""

import sys
sys.path.insert(0, '.')

from chatbot.utils.formatting import sanitize_markdown

# Test cases with various markdown patterns
test_cases = [
    ("***bold italic***", "bold italic"),
    ("**bold text**", "bold text"),
    ("*italic text*", "italic text"),
    ("# Heading", "Heading"),
    ("• Bullet point", "Bullet point"),
    ("1. Numbered item", "Numbered item"),
    ("[Link](http://example.com)", "Link"),
    ("`code`", "code"),
    ("Text with ***triple asterisks*** in middle", "Text with triple asterisks in middle"),
    ("Text with **double asterisks** in middle", "Text with double asterisks in middle"),
    ("Text with *single asterisk* in middle", "Text with single asterisk in middle"),
    ("Multiple ***bold*** and **text** and *italic*", "Multiple bold and text and italic"),
    ("*** standalone asterisks ***", "standalone asterisks"),
    ("PM-Kisan Scheme ***with asterisks***", "PM-Kisan Scheme with asterisks"),
]

print("=" * 70)
print("MARKDOWN REMOVAL TEST")
print("=" * 70)

passed = 0
failed = 0

for input_text, expected in test_cases:
    result = sanitize_markdown(input_text)
    status = "✅ PASS" if result == expected else "❌ FAIL"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"\n{status}")
    print(f"Input:    {input_text}")
    print(f"Expected: {expected}")
    print(f"Got:      {result}")

print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed out of {len(test_cases)}")
print("=" * 70)

if failed == 0:
    print("\n🎉 All tests passed! Markdown removal is working correctly.")
else:
    print(f"\n⚠️ {failed} test(s) failed.")
