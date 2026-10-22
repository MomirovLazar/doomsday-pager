
"""Unit tests for incident workflow operations."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from constants import IncidentStatus, IncidentResponse
from services.incident_service import (
    claim_incident_record,
    join_incident_record,
    request_incident_help,
    resolve_incident_record,
    respond_to_incident
)

@pytest.fixture
def db():
    return MagicMock()


@pytest.fixture
def user():
    return SimpleNamespace(id=7, username="test_admin")


def test_claim_incident_success(db, user):
    db.scalar.return_value = 42

    result = claim_incident_record(
        incident_id=42,
        db=db,
        current_user=user,
    )

    assert result["incident_id"] == 42
    assert result["status"] == IncidentStatus.IN_PROGRESS
    assert result["owner"]["id"] == user.id

    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_claim_incident_not_found(db, user):
    db.scalar.return_value = None
    db.get.return_value = None

    with pytest.raises(HTTPException) as exc:
        claim_incident_record(42, db, user)

    assert exc.value.status_code == 404
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_claim_incident_conflict(db, user):
    db.scalar.return_value = None
    db.get.return_value = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=9,
    )

    with pytest.raises(HTTPException) as exc:
        claim_incident_record(42, db, user)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_join_incident_success(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=9,
    )

    db.scalar.side_effect = [incident, None]

    responder = SimpleNamespace(
        joined_at="2026-10-22T10:00:00",
    )
    db.refresh.side_effect = lambda obj: setattr(
        obj, "joined_at", responder.joined_at
    )

    result = join_incident_record(
        incident_id=42,
        db=db,
        current_user=user,
    )

    assert result["incident_id"] == 42
    assert result["responder"]["id"] == user.id
    assert result["message"] == "Successfully joined incident"

    db.commit.assert_called_once()
    db.rollback.assert_not_called()
    assert db.add.call_count == 2


def test_join_incident_not_found(db, user):
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        join_incident_record(42, db, user)

    assert exc.value.status_code == 404
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_join_incident_already_joined(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=9,
    )

    existing_responder = SimpleNamespace(
        incident_id=42,
        user_id=user.id,
    )

    db.scalar.side_effect = [
        incident,
        existing_responder,
    ]

    with pytest.raises(HTTPException) as exc:
        join_incident_record(42, db, user)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_join_incident_owner_cannot_join(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=user.id,
    )

    db.scalar.return_value = incident

    with pytest.raises(HTTPException) as exc:
        join_incident_record(42, db, user)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_request_help_success(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=user.id,
    )

    db.scalar.side_effect = [incident, None]

    result = request_incident_help(42, db, user)

    assert result["incident_id"] == 42
    assert result["help_requested"] is True
    assert result["requested_by"]["id"] == user.id

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_request_help_not_found(db, user):
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        request_incident_help(42, db, user)

    assert exc.value.status_code == 404
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_request_help_not_owner(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=99,
    )

    db.scalar.return_value = incident

    with pytest.raises(HTTPException) as exc:
        request_incident_help(42, db, user)

    assert exc.value.status_code == 403
    db.rollback.assert_called_once()
    db.commit.assert_not_called()

def test_request_help_already_requested(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=user.id,
    )

    existing_request = SimpleNamespace(id=5)

    db.scalar.side_effect = [incident, existing_request]

    with pytest.raises(HTTPException) as exc:
        request_incident_help(42, db, user)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_resolve_incident_success(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=user.id,
        resolved_at=None,
    )

    db.scalar.return_value = incident

    result = resolve_incident_record(42, db, user)

    assert result["incident_id"] == 42
    assert result["status"] == IncidentStatus.RESOLVED
    assert result["resolved_by"]["id"] == user.id
    assert result["resolved_at"] is not None

    assert incident.status == IncidentStatus.RESOLVED
    assert incident.resolved_at is not None

    db.add.assert_called_once()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_resolve_incident_not_found(db, user):
    db.scalar.return_value = None

    with pytest.raises(HTTPException) as exc:
        resolve_incident_record(42, db, user)

    assert exc.value.status_code == 404
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_resolve_incident_not_owner(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.IN_PROGRESS,
        owner_id=99,
    )

    db.scalar.return_value = incident

    with pytest.raises(HTTPException) as exc:
        resolve_incident_record(42, db, user)

    assert exc.value.status_code == 403
    db.rollback.assert_called_once()
    db.commit.assert_not_called()


def test_resolve_incident_wrong_status(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.RESOLVED,
        owner_id=user.id,
    )

    db.scalar.return_value = incident

    with pytest.raises(HTTPException) as exc:
        resolve_incident_record(42, db, user)

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()

def test_cannot_respond_to_resolved_incident(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.RESOLVED,
    )

    db.scalar.return_value = incident

    with pytest.raises(HTTPException) as exc:
        respond_to_incident(
            incident_id=42,
            response=IncidentResponse.ACKNOWLEDGED,
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()

def test_duplicate_ack_does_not_create_new_record(db, user):
    responded_at = "2026-10-22T12:00:00"

    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.NEW,
    )

    existing_response = SimpleNamespace(
        response=IncidentResponse.ACKNOWLEDGED,
        responded_at=responded_at,
        acknowledged_at=responded_at,
    )

    db.scalar.side_effect = [
        incident,
        existing_response,
    ]

    result = respond_to_incident(
        incident_id=42,
        response=IncidentResponse.ACKNOWLEDGED,
        db=db,
        current_user=user,
    )

    assert result["message"] == "Response already recorded"
    assert result["response"] == IncidentResponse.ACKNOWLEDGED

    db.add.assert_not_called()
    db.commit.assert_called_once()
    db.rollback.assert_not_called()

def test_ack_cannot_change_to_unavailable(db, user):
    incident = SimpleNamespace(
        id=42,
        status=IncidentStatus.NEW,
    )

    existing_response = SimpleNamespace(
        response=IncidentResponse.ACKNOWLEDGED,
    )

    db.scalar.side_effect = [
        incident,
        existing_response,
    ]

    with pytest.raises(HTTPException) as exc:
        respond_to_incident(
            incident_id=42,
            response=IncidentResponse.UNAVAILABLE,
            db=db,
            current_user=user,
        )

    assert exc.value.status_code == 409
    db.rollback.assert_called_once()
    db.commit.assert_not_called()