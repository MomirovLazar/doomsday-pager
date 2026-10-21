
"""Unit tests for incident response business rules."""

from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from constants import AuditAction, IncidentResponse
from models import AuditLog, IncidentAcknowledgement
from services.incident_service import respond_to_incident


@pytest.fixture
def db():
    """Provide a mocked database session."""
    return MagicMock()


@pytest.fixture
def current_user():
    """Provide a minimal authenticated user."""
    user = MagicMock()
    user.id = 10
    return user


def test_acknowledge_creates_response(db, current_user):
    """A first acknowledgement creates a response and audit event."""
    db.scalar.side_effect = [
        MagicMock(),  # Existing incident
        None,         # No previous response
    ]

    result = respond_to_incident(
        incident_id=1,
        response=IncidentResponse.ACKNOWLEDGED,
        db=db,
        current_user=current_user,
    )

    assert result["response"] == IncidentResponse.ACKNOWLEDGED
    assert result["acknowledged_at"] is not None

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    acknowledgements = [
        obj for obj in added_objects
        if isinstance(obj, IncidentAcknowledgement)
    ]

    audits = [
        obj for obj in added_objects
        if isinstance(obj, AuditLog)
    ]

    assert len(acknowledgements) == 1
    assert len(audits) == 1
    assert audits[0].action == AuditAction.INCIDENT_ACKNOWLEDGED
    db.commit.assert_called_once()


def test_repeated_acknowledgement_is_idempotent(db, current_user):
    """Repeating the same response must not create another record."""
    existing = IncidentAcknowledgement(
        incident_id=1,
        user_id=current_user.id,
        response=IncidentResponse.ACKNOWLEDGED,
    )

    db.scalar.side_effect = [
        MagicMock(),
        existing,
    ]

    result = respond_to_incident(
        incident_id=1,
        response=IncidentResponse.ACKNOWLEDGED,
        db=db,
        current_user=current_user,
    )

    assert result["message"] == "Response already recorded"
    db.add.assert_not_called()
    db.commit.assert_called_once()


def test_acknowledged_cannot_become_unavailable(db, current_user):
    """An acknowledged response cannot be downgraded."""
    existing = IncidentAcknowledgement(
        incident_id=1,
        user_id=current_user.id,
        response=IncidentResponse.ACKNOWLEDGED,
    )

    db.scalar.side_effect = [
        MagicMock(),
        existing,
    ]

    with pytest.raises(HTTPException) as exc_info:
        respond_to_incident(
            incident_id=1,
            response=IncidentResponse.UNAVAILABLE,
            db=db,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_missing_incident_returns_404(db, current_user):
    """A response cannot be recorded for a missing incident."""
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        respond_to_incident(
            incident_id=999,
            response=IncidentResponse.ACKNOWLEDGED,
            db=db,
            current_user=current_user,
        )

    assert exc_info.value.status_code == 404
    db.rollback.assert_called_once()
    db.commit.assert_not_called()
