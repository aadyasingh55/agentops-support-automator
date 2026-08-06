def plan_workflow(signals: dict[str, bool]) -> dict[str, str]:
    if signals.get("mentions_outage"):
        return {"category": "incident", "priority": "urgent", "risk": "high"}
    if signals.get("mentions_auth"):
        return {"category": "authentication", "priority": "high", "risk": "high"}
    if signals.get("mentions_payment"):
        return {"category": "billing", "priority": "medium", "risk": "medium"}
    return {"category": "product_support", "priority": "normal", "risk": "low"}
