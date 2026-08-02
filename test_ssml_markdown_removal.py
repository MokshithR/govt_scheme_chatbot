"""
Comprehensive test for markdown removal in SSML voice output
Tests all Gemini response types to ensure clean text for voice synthesis
"""

import sys
sys.path.insert(0, '.')

from chatbot.utils.formatting import sanitize_markdown

# Test cases simulating various Gemini response patterns
test_cases = [
    {
        "name": "Headers",
        "input": "### Agricultural Schemes\n## PM Kisan\n# Benefits",
        "should_not_contain": ["###", "##", "#"]
    },
    {
        "name": "Bold and Italic",
        "input": "**PM Kisan** provides *financial support* to farmers",
        "should_not_contain": ["**", "*"]
    },
    {
        "name": "Bullets",
        "input": "Benefits:\n• Direct cash transfer\n• ₹6000 per year\n• Easy application",
        "should_not_contain": ["•"]
    },
    {
        "name": "Dashes",
        "input": "Benefits:\n- Direct cash transfer\n- ₹6000 per year\n- Easy application",
        "should_not_contain": ["-"]
    },
    {
        "name": "Numbered Lists",
        "input": "Steps:\n1. Register online\n2. Submit documents\n3. Wait for approval",
        "should_not_contain": ["1.", "2.", "3."]
    },
    {
        "name": "Table Pipes",
        "input": "| Scheme | Benefit | Eligibility |\n| PM Kisan | ₹6000 | Farmers |",
        "should_not_contain": ["|"]
    },
    {
        "name": "Mixed Formatting",
        "input": "**PM Kisan Samman Nidhi**\n\n### Eligibility:\n- Farmers with cultivable land\n- *All states* included\n\n### Benefits:\n1. ₹6000 per year\n2. Direct bank transfer",
        "should_not_contain": ["**", "###", "-", "*", "1.", "2."]
    },
    {
        "name": "Links",
        "input": "Apply at [PM Kisan Portal](https://pmkisan.gov.in)",
        "should_not_contain": ["[", "]", "(", ")"]
    },
    {
        "name": "Code blocks",
        "input": "Example: `pm-kisan-scheme`\n```\nScheme code: KCC001\n```",
        "should_not_contain": ["`", "```"]
    },
    {
        "name": "Triple asterisks",
        "input": "***Important Notice*** about the scheme",
        "should_not_contain": ["***", "**", "*"]
    }
]

print("=" * 80)
print("SSML VOICE OUTPUT - MARKDOWN REMOVAL TEST")
print("=" * 80)

total_passed = 0
total_failed = 0

for test in test_cases:
    print(f"\n📋 TEST: {test['name']}")
    print("-" * 80)
    
    input_text = test['input']
    cleaned = sanitize_markdown(input_text)
    
    print(f"Input:   {input_text[:60]}...")
    print(f"Output:  {cleaned[:60]}...")
    
    # Check for forbidden symbols
    failed_checks = []
    for symbol in test['should_not_contain']:
        if symbol in cleaned:
            failed_checks.append(symbol)
    
    if failed_checks:
        print(f"❌ FAIL - Found forbidden symbols: {', '.join(failed_checks)}")
        total_failed += 1
    else:
        print(f"✅ PASS - Clean text for voice synthesis")
        total_passed += 1

print("\n" + "=" * 80)
print("FINAL RESULTS")
print("=" * 80)
print(f"✅ Passed: {total_passed}/{len(test_cases)}")
print(f"❌ Failed: {total_failed}/{len(test_cases)}")

if total_failed == 0:
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ SSML voice output will be clean and natural")
    print("✅ No markdown symbols will be spoken")
else:
    print(f"\n⚠️  {total_failed} test(s) failed - review sanitization logic")

# Additional SSML safety check
print("\n" + "=" * 80)
print("SSML SAFETY CHECK")
print("=" * 80)

ssml_dangerous = ["<", ">", "&", '"', "'"]
sample_text = "**PM Kisan** provides <₹6000> per year & has 'easy' application"
cleaned_sample = sanitize_markdown(sample_text)

print(f"Input:  {sample_text}")
print(f"Output: {cleaned_sample}")

ssml_safe = True
for char in ssml_dangerous:
    if char in cleaned_sample and char not in ["₹", "6000"]:  # Allow currency
        print(f"⚠️  Warning: Found SSML-unsafe character: {char}")
        ssml_safe = False

if ssml_safe:
    print("✅ Output is safe for SSML wrapping")
else:
    print("⚠️  Output may need HTML entity escaping for SSML")

print("\n" + "=" * 80)
