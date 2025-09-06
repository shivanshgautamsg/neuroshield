# nlp_sentiment.py
from textblob import TextBlob

def analyze_sentiment(text):
    """
    Returns sentiment polarity (-1 to 1) and threat level (0 to 1).
    Threat level is positive if text is negative.
    """
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity  # -1 to 1
    # threat_level: negative polarity = higher threat
    threat_level = max(0, -polarity)
    return {"polarity": polarity, "threat_level": threat_level}
