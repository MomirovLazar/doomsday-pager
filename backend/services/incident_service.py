"""Business operations for incident management."""

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from constants import AuditAction, IncidentResponse
from models import (
    AuditLog,
    Incident,
    IncidentAcknowledgement,
    User,
)

def respond_to_incident(incident_id: int, response: IncidentResponse, db:Session, current_user: User):

    try:
        incident = db.scalar(
            select(Incident).where(Incident.id == incident_id).with_for_update()
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        existing_response = db.scalar(
            select(IncidentAcknowledgement).where(
                IncidentAcknowledgement.incident_id == incident_id,
                IncidentAcknowledgement.user_id == current_user.id
            )
        )

        if existing_response is not None:
            if existing_response.response == response:
                db.commit()

                return {
                    "incident_id": incident_id,
                    "response": existing_response.response,
                    "responded_at": existing_response.responded_at,
                    "acknowledged_at": existing_response.acknowledged_at,
                    "message": "Response already recorded"
                }

            if existing_response.response == IncidentResponse.ACKNOWLEDGED:
                raise HTTPException(
                    status_code=409,
                    detail="Acknowledged response cannot be change to unavailable"
                )

        now = datetime.now(timezone.utc)

        if existing_response is None:
            existing_response = IncidentAcknowledgement(
                incident_id=incident_id,
                user_id=current_user.id,
                response=response,
                responded_at=now,
                acknowledged_at=(
                    now if response == IncidentResponse.ACKNOWLEDGED else None
                )
            )

            db.add(existing_response)

        else:
            existing_response.response = response
            existing_response.responded_at = now

            if response == IncidentResponse.ACKNOWLEDGED:
                existing_response.acknowledged_at = now

        audit_action = (
            AuditAction.INCIDENT_ACKNOWLEDGED

            if response == IncidentResponse.ACKNOWLEDGED
            else AuditAction.INCIDENT_UNAVAILABLE
        )

        db.add(
            AuditLog(
                incident_id=incident_id,
                actor_id=current_user.id,
                action=audit_action,
                details=f"User responded: {response.value}"
            )
        )

        db.commit()
        db.refresh(existing_response)

        return {
            "incident_id": incident_id,
            "response": existing_response.response,
            "responded_at": existing_response.responded_at,
            "acknowledged_at": existing_response.acknowledged_at,
            "message": "Incident response recorded successfully"
        }

    except Exception:
        db.rollback()
        raise
