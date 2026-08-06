def ingest_ticket(title: str, body: str) -> dict[str, object]:
    text = f"{title}\n{body}".lower()
    signals = {
        "mentions_auth": any(word in text for word in ["auth", "login", "token", "jwt"]),
        "mentions_payment": any(word in text for word in ["payment", "billing", "invoice"]),
        "mentions_outage": any(word in text for word in ["down", "outage", "unavailable", "500"]),
    }
    return {
        "normalized_summary": " ".join(body.split())[:280],
        "signals": signals,
        "confidence": 0.86,
    }
