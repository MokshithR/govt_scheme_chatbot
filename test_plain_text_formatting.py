"""
Test Plain Text Formatting (No Markdown)
========================================
Quick test to verify all markdown has been removed from chatbot responses.
"""

import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'govt_voice_chatbot.settings')
django.setup()

from chatbot.models import GovernmentScheme
from chatbot.utils.formatting import (
    format_scheme_answer,
    format_multiple_schemes,
    format_fallback_message,
    remove_markdown,
    format_eligibility_plain,
    format_benefits_plain
)
from chatbot.query_helpers import generate_friendly_intro


def check_no_markdown(text: str, test_name: str) -> bool:
    """Check if text contains any markdown symbols."""
    markdown_symbols = ['**', '*', '•', '#', '__', '_']
    has_markdown = False
    
    for symbol in markdown_symbols:
        if symbol in text:
            print(f"❌ {test_name}: Found markdown symbol '{symbol}'")
            has_markdown = True
    
    if not has_markdown:
        print(f"✅ {test_name}: Clean plain text (no markdown)")
    
    return not has_markdown


def test_format_scheme_answer():
    """Test format_scheme_answer returns plain text."""
    print("\n" + "="*60)
    print("TEST 1: format_scheme_answer()")
    print("="*60)
    
    # Get first scheme
    scheme = GovernmentScheme.objects.filter(is_active=True).first()
    
    if not scheme:
        print("⚠️  No schemes found in database")
        return False
    
    formatted = format_scheme_answer(scheme, include_llm_enhancement=False)
    print(f"\nFormatted output:\n{formatted[:500]}...")
    
    return check_no_markdown(formatted, "format_scheme_answer")


def test_format_multiple_schemes():
    """Test format_multiple_schemes returns plain text."""
    print("\n" + "="*60)
    print("TEST 2: format_multiple_schemes()")
    print("="*60)
    
    schemes = GovernmentScheme.objects.filter(is_active=True)[:3]
    
    if not schemes.exists():
        print("⚠️  No schemes found in database")
        return False
    
    formatted = format_multiple_schemes(schemes, max_schemes=3)
    print(f"\nFormatted output:\n{formatted[:500]}...")
    
    return check_no_markdown(formatted, "format_multiple_schemes")


def test_generate_friendly_intro():
    """Test generate_friendly_intro returns plain text."""
    print("\n" + "="*60)
    print("TEST 3: generate_friendly_intro()")
    print("="*60)
    
    test_cases = [
        ('exact_match', {'scheme_title': 'PM-KISAN'}),
        ('fuzzy_match', {'scheme_title': 'Ayushman Bharat'}),
        ('sector_match', {'sector': 'Agriculture', 'count': 5}),
        ('vector_match', {'count': 3}),
    ]
    
    all_clean = True
    
    for match_type, kwargs in test_cases:
        intro = generate_friendly_intro(match_type, **kwargs)
        print(f"\n{match_type}: {intro}")
        
        is_clean = check_no_markdown(intro, f"friendly_intro({match_type})")
        all_clean = all_clean and is_clean
    
    return all_clean


def test_format_fallback_message():
    """Test format_fallback_message returns plain text."""
    print("\n" + "="*60)
    print("TEST 4: format_fallback_message()")
    print("="*60)
    
    formatted = format_fallback_message("xyz unknown scheme")
    print(f"\nFormatted output:\n{formatted}")
    
    return check_no_markdown(formatted, "format_fallback_message")


def test_remove_markdown():
    """Test remove_markdown function."""
    print("\n" + "="*60)
    print("TEST 5: remove_markdown()")
    print("="*60)
    
    test_cases = [
        ("**Bold text**", "Bold text"),
        ("*Italic text*", "Italic text"),
        ("• Bullet point", "Bullet point"),
        ("1. Numbered item", "Numbered item"),
        ("### Header", "Header"),
        ("[Link](http://example.com)", "Link"),
        ("`code`", "code"),
    ]
    
    all_passed = True
    
    for markdown_text, expected in test_cases:
        result = remove_markdown(markdown_text)
        passed = expected in result or result == expected
        
        status = "✅" if passed else "❌"
        print(f"{status} '{markdown_text}' → '{result}' (expected: '{expected}')")
        
        all_passed = all_passed and passed
    
    return all_passed


def test_helper_functions():
    """Test format_eligibility_plain and format_benefits_plain."""
    print("\n" + "="*60)
    print("TEST 6: Helper Functions")
    print("="*60)
    
    # Test eligibility
    eligibility_text = "**Small farmers** with • cultivable land • up to 2 hectares"
    eligibility_plain = format_eligibility_plain(eligibility_text)
    print(f"\nEligibility (plain): {eligibility_plain}")
    check1 = check_no_markdown(eligibility_plain, "format_eligibility_plain")
    
    # Test benefits
    benefits_text = "**Financial assistance:** • ₹6000/year • **Direct transfer** • No middleman"
    benefits_plain = format_benefits_plain(benefits_text)
    print(f"\nBenefits (plain): {benefits_plain}")
    check2 = check_no_markdown(benefits_plain, "format_benefits_plain")
    
    return check1 and check2


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("PLAIN TEXT FORMATTING TEST SUITE")
    print("="*60)
    print("Verifying NO markdown symbols (**, *, •, #, _, etc.)")
    print("="*60)
    
    results = {
        'format_scheme_answer': test_format_scheme_answer(),
        'format_multiple_schemes': test_format_multiple_schemes(),
        'generate_friendly_intro': test_generate_friendly_intro(),
        'format_fallback_message': test_format_fallback_message(),
        'remove_markdown': test_remove_markdown(),
        'helper_functions': test_helper_functions(),
    }
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✅ PASS" if passed_test else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\n{passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! All markdown removed successfully!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review output above.")


if __name__ == '__main__':
    main()
