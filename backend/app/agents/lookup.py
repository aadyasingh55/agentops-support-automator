def lookup_evidence(category: str) -> list[str]:
    evidence = {
        "incident": [
            "Check current health endpoint status.",
            "Review recent deployment and infrastructure logs.",
            "Prepare customer-facing incident acknowledgement.",
        ],
        "authentication": [
            "Inspect token expiry and middleware changes.",
            "Confirm affected account scope.",
            "Avoid executing auth changes without reviewer approval.",
        ],
        "billing": [
            "Compare invoice state against payment provider status.",
            "Confirm duplicate charge or failed payment evidence.",
        ],
        "product_support": [
            "Search documentation and known issues.",
            "Draft reproducible steps before proposing a fix.",
        ],
    }
    return evidence.get(category, evidence["product_support"])
