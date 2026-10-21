"""Business operations for incident management."""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from constants import AuditAction, IncidentResponse, IncidentStatus, UserRole
from models import (
    AuditLog,
    Incident,
    IncidentAcknowledgement,
    User,
    IncidentResponder,
    Comment
)

from schemas import IncidentCreate, CommentCreate

def get_locked_incident(incident_id: int, db: Session,) -> Incident:

   incident = db.scalar(
       select(Incident).where(Incident.id == incident_id).with_for_update()
   ) 

   if incident is None:
       raise HTTPException(
           status_code=status.HTTP_404_NOT_FOUND,
           detail="Incident not found",
       )

   return incident

def create_incident_record(incident_data: IncidentCreate, db: Session, current_user: User) -> dict:

    incident = Incident(
            title=incident_data.title.strip(),
            description=incident_data.description.strip(),
            type=incident_data.type,
            priority=incident_data.priority,
            status=IncidentStatus.NEW,
            created_by_id=current_user.id,
            owner_id = None 
        )
    
    try:
        db.add(incident)
        db.flush()

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            action=AuditAction.INCIDENT_CREATED,
            details="Incident created"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "type": incident.type,
        "priority": incident.priority,
        "status": incident.status,
        "created_by_id": incident.created_by_id,
        "owner_id": incident.owner_id
    }

def get_incident_details(incident_id: int, db: Session, current_user: User,) -> dict:
    
    is_admin = current_user.role.name == UserRole.ADMIN

    load_options = [
        selectinload(Incident.creator),
        selectinload(Incident.owner),
        selectinload(Incident.responders).selectinload(IncidentResponder.user),
        selectinload(Incident.comments).selectinload(Comment.author),
        selectinload(Incident.audit_logs),
    ]

    if is_admin:
        load_options.append(
            selectinload(Incident.audit_logs).selectinload(AuditLog.actor)
        )

    incident = db.scalar(
        select(Incident).options(*load_options).where(Incident.id == incident_id)
    )
    
    if incident is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND
        )

    responders = []

    for responder in incident.responders:
        responders.append({
            "id": responder.user.id,
            "username": responder.user.username,
            "joined_at": responder.joined_at
        })

    comments = []

    for comment in sorted(incident.comments, key=lambda item: item.created_at):
        comments.append({
            "id": comment.id,
            "author": comment.author.username,
            "content": comment.content,
            "created_at": comment.created_at
        })

    history = []

    if is_admin:
        for event in sorted(incident.audit_logs, key=lambda item: item.created_at):
            history.append({
                "id": event.id,
                "action": event.action,
                "performed_by": (
                    event.actor.username

                    if event.actor is not None
                    else "SYSTEM"
                ),
                "details": event.details,
                "created_at": event.created_at
            })

    responses = db.scalars(
        select(IncidentAcknowledgement)
        .where(IncidentAcknowledgement.incident_id == incident_id)
        .options(selectinload(IncidentAcknowledgement.user))
    ).all()

    response_data = []

    for item in responses:
        response_data.append({
            "user": {
                "id": item.user.id,
                "username": item.user.username
            },
            "response": item.response,
            "responded_at": item.responded_at,
            "acknowledged_at": item.acknowledged_at
        })

    owner_data = None   

    if incident.owner is not None:
        owner_data = {
            "id": incident.owner.id,
            "username": incident.owner.username
        }

    my_response = next((
       item["response"]
       for item in response_data
       if item["user"]["id"] == current_user.id
    ), None
   )

    help_requested = any(
        event.action == AuditAction.HELP_REQUESTED
        for event in incident.audit_logs
    )

    return {
        "id": incident.id,
        "title": incident.title,
        "description": incident.description,
        "type": incident.type,
        "priority": incident.priority,
        "status": incident.status,
        "created_by": {
            "id": incident.creator.id,
            "username": incident.creator.username
        },
        "owner": owner_data,
        "responders": responders,
        "comments": comments,
        "history": history,
        "created_at": incident.created_at,
        "resolved_at": incident.resolved_at,
        "responses": response_data,
        "my_response": my_response,
        "help_requested": help_requested
    }

def claim_incident_record(incident_id:int, db: Session, current_user: User,) -> dict:
    try:
        statement = (
            update(Incident).where(
                Incident.id == incident_id,
                Incident.owner_id.is_(None),
                Incident.status == IncidentStatus.NEW
            ).values(
                owner_id = current_user.id,
                status=IncidentStatus.IN_PROGRESS
            ).returning(
                Incident.id
            )
        )

        claimed_id = db.scalar(statement)

        if claimed_id is None:
            incident = db.get(Incident, incident_id)

            if incident is None:
                raise HTTPException(
                    status_code=404,
                    detail="Incident not found"
                )

            raise HTTPException(
                status_code=409,
                detail="Incident cannot be claimed"
            )

        audit = AuditLog(
            incident_id=claimed_id,
            actor_id=current_user.id,
            action=AuditAction.INCIDENT_CLAIMED,
            details="Incident claimed by responder"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise   

    return{
        "incident_id": claimed_id,
        "status": IncidentStatus.IN_PROGRESS,
        "owner": {  
            "id": current_user.id,
            "username": current_user.username
        },
        "message": "Incident claimed successfully"
    }

def respond_to_incident(incident_id: int, response: IncidentResponse, db:Session, current_user: User):

    try:
        incident = get_locked_incident(incident_id, db)

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

def join_incident_record(incident_id: int, db: Session, current_user: User,):
    try:
        incident = get_locked_incident(incident_id, db)

        if incident.status != IncidentStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=409,
                detail="Incident not in progress"
            )

        if incident.owner_id == current_user.id:
            raise HTTPException(
                status_code=409,
                detail="Owner is already responsible for this incident"
            )

        existing_responder = db.scalar(
            select(IncidentResponder).where(
                IncidentResponder.incident_id == incident_id,
                IncidentResponder.user_id == current_user.id
            )
        )

        if existing_responder is not None:
            raise HTTPException(
                status_code=409,
                detail="User already joined this incident"
            )

        responder = IncidentResponder(
            incident_id = incident_id,
            user_id = current_user.id
        )

        db.add(responder)

        audit = AuditLog(
            incident_id=incident_id,
            actor_id = current_user.id,
            action=AuditAction.RESPONDER_JOINED,
            details="User joined incident as responder"
        )

        db.add(audit)
        db.commit()
        db.refresh(responder)

    except Exception:
        db.rollback()
        raise

    return {
        "incident_id": incident_id,
        "responder": {
            "id": current_user.id,
            "username": current_user.username
        },
        "joined_at": responder.joined_at,
        "message": "Successfully joined incident"
    }


def get_incidents_list(db: Session) -> list[dict]:

    incidents = db.scalars(
        select(Incident)
        .options(
            selectinload(Incident.creator),
            selectinload(Incident.owner),
        )
        .order_by(Incident.created_at.desc())
    ).all()

    result = []

    for incident in incidents:
        owner_data = None

        if incident.owner is not None:
            owner_data = {
                "id": incident.owner.id,
                "username": incident.owner.username,
            }

        result.append(
            {
                "id": incident.id,
                "title": incident.title,
                "type": incident.type,
                "priority": incident.priority,
                "status": incident.status,
                "created_by": {
                    "id": incident.created_by_id,
                    "username": incident.creator.username,
                },
                "owner": owner_data,
                "created_at": incident.created_at,
            }
        )

    return result

def request_incident_help(incident_id: int, db: Session, current_user: User,):
    try:
        incident = get_locked_incident(incident_id, db)

        if incident.status != IncidentStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=409,
                detail="Incident is not in progress"
            )

        if incident.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only incident owner can request help"
            )

        existing_request = db.scalar(
            select(AuditLog).where(
                AuditLog.incident_id == incident_id,
                AuditLog.action == AuditAction.HELP_REQUESTED
            )
        )

        if existing_request is not None:
            raise HTTPException(
                status_code=409,
                detail="Help has already been requested"
            )

        audit = AuditLog(
            incident_id=incident_id,
            actor_id=current_user.id,
            action=AuditAction.HELP_REQUESTED,
            details="Incident owner requested additional help"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "incident_id": incident_id,
        "help_requested": True,
        "requested_by": {
            "id": current_user.id,
            "username": current_user.username
        },
        "message": "Help requested successfully"
    }

def add_incident_comment(incident_id: int, comment_data: CommentCreate, db: Session, current_user: User,):
    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        comment = Comment(
            incident_id=incident_id,
            author_id=current_user.id,
            content=comment_data.content
        )

        db.add(comment)
        db.flush()

        audit = AuditLog(
            incident_id=incident_id,
            actor_id=current_user.id,
            action=AuditAction.COMMENT_ADDED,
            details=f"Comment added: {comment.id}"
        )

        db.add(audit)
        db.commit()
        db.refresh(comment)

    except Exception:
        db.rollback()
        raise 

    return {
        "id": comment.id,
        "incident_id": incident_id,
        "author": current_user.username,
        "content": comment.content,
        "created_at": comment.created_at
    }

def resolve_incident_record(incident_id: int, db: Session, current_user: User,):
    try:
        incident = get_locked_incident(incident_id, db)

        if incident.owner_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the incident owner can resolve it"
            )

        if incident.status != IncidentStatus.IN_PROGRESS:
            raise HTTPException(
                status_code=409,
                detail="Only incidents in progress can be resolved"
            )

        incident.status = IncidentStatus.RESOLVED
        incident.resolved_at = datetime.now(timezone.utc)

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            action=AuditAction.INCIDENT_RESOLVED,
            details="Incident resolved by owner"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "incident_id": incident.id,
        "status": incident.status,
        "resolved_at": incident.resolved_at,
        "resolved_by": {
            "id": current_user.id,
            "username": current_user.username
        }
    }