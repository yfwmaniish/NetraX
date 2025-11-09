from ai_utils import get_threat_score_from_gemini

keywords = ['drugs', 'bitcoin', 'weapons']
score = get_threat_score_from_gemini(keywords)
print(f"Threat Score: {score}")
