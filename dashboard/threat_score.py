import spacy
import json
import re

nlp = spacy.load("en_core_web_sm")

# Load keywords as a flat list (you already fixed the JSON)
with open("keywords.json") as f:
    raw = json.load(f)
    terms = raw["terms"] if isinstance(raw, dict) else raw

pii_labels = {"PERSON", "EMAIL", "GPE", "ORG", "PHONE_NUMBER"}

def calculate_threat_score(text: str) -> tuple:
    score = 0
    matched_keywords = []
    lowered_text = text.lower()

    # ✅ Match exact keywords from list (case-insensitive)
    for word in terms:
        pattern = r"\\b" + re.escape(word.lower()) + r"\\b"
        if re.search(pattern, lowered_text):
            score += 10
            matched_keywords.append(word)

    # ✅ Add small score for PII-based entities (not added to reasons)
    doc = nlp(text)
    for ent in doc.ents:
        if ent.label_ in pii_labels:
            score += 5

    return min(score, 100), matched_keywords

