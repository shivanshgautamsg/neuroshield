# nlp_utils.py
def summarize_text(text):
    return text.split(".")[0][:240] + ("..." if len(text)>240 else "")

def classify_intent(text):
    t = text.lower()
    if any(w in t for w in ["murder","shoot","stab","bomb","blast","terror"]):
        return "violent"
    if any(w in t for w in ["snatch","robbery","rob","theft","snatching"]):
        return "property"
    if any(w in t for w in ["scam","fraud","phishing","fake"]):
        return "cyber"
    return "other"
