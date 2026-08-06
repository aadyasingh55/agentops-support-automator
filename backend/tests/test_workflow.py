from app.services.workflow import build_support_workflow


def test_support_workflow_pauses_high_risk_auth_ticket_for_review() -> None:
    workflow = build_support_workflow()

    result = workflow.invoke(
        {
            "title": "Auth failure after deploy",
            "body": "JWT token refresh is failing and users cannot login.",
        }
    )

    assert result["category"] == "authentication"
    assert result["priority"] == "high"
    assert result["risk"] == "high"
    assert result["status"] == "awaiting_review"
    assert "Evidence checklist" in result["draft_response"]
