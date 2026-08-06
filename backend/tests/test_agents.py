from app.agents.ingestion import ingest_ticket
from app.agents.planner import plan_workflow


def test_ingestion_extracts_auth_signal() -> None:
    result = ingest_ticket(
        "Login failure",
        "Users cannot login after JWT token refresh.",
    )

    assert result["signals"]["mentions_auth"] is True
    assert result["confidence"] >= 0.8


def test_planner_routes_outages_as_urgent_incidents() -> None:
    result = plan_workflow(
        {
            "mentions_auth": False,
            "mentions_payment": False,
            "mentions_outage": True,
        }
    )

    assert result == {
        "category": "incident",
        "priority": "urgent",
        "risk": "high",
    }
