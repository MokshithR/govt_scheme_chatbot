"""ML parsing helpers to extract structured fields from scheme text.
This is a scaffold with a simple rule-based fallback and a placeholder for model-based parsing.
"""
import re
from typing import Dict


def extract_ministry(text: str) -> str:
    # very simple heuristic: look for patterns like 'Ministry of X' or 'Ministry:'
    m = re.search(r'(Ministry of [A-Za-z &]+)', text, re.I)
    if m:
        return m.group(1)
    m2 = re.search(r'Ministry[:\s]+([A-Za-z &]+)', text, re.I)
    if m2:
        return m2.group(1)
    return ''


def extract_department(text: str) -> str:
    m = re.search(r'Department of [A-Za-z &]+', text, re.I)
    if m:
        return m.group(0)
    return ''


def parse_scheme_text(title: str, description: str) -> Dict:
    """Return parsed fields for a scheme using heuristics (placeholder for ML model).
    """
    combined = f"{title}\n{description}"
    return {
        'ministry': extract_ministry(combined),
        'department': extract_department(combined),
    }
