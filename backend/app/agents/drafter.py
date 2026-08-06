def draft_response(category: str, priority: str, risk: str, evidence: list[str]) -> str:
    evidence_lines = "\n".join(f"- {item}" for item in evidence)
    return (
        f"Category: {category}\n"
        f"Priority: {priority}\n"
        f"Risk: {risk}\n\n"
        "Proposed action:\n"
        "Acknowledge the report, validate the scope, and proceed through the "
        "review gate before any risky execution.\n\n"
        f"Evidence checklist:\n{evidence_lines}"
    )
