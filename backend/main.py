from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from auth import authenticate_user
from database import get_db
from schemas import LoginRequest, IncidentCreate

from jwt_handler import create_access_token
from dependencies import get_current_user, require_roles
from models import (
    User, 
    Incident, 
    IncidentResponder, 
    Comment, 
    AuditLog,
    IncidentAcknowledgement    
)

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Doomsday Pager API is running"}

@app.post("/login")
def login(credentials: LoginRequest, db: Session = Depends(get_db)):

    user = authenticate_user(
        db, 
        credentials.username,
        credentials.password
    )

    if user is None:
        raise HTTPException(
            status_code=status.     HTTP_401_UNAUTHORIZED,
            detail="Invaild username or password"
        )

    access_token = create_access_token(user.id)

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@app.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    
    return{
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role.name
    }

@app.get("/admin-only")
def admin_only(
    current_user: User = Depends(require_roles("ADMIN"))
):
    return {
        "message": "Welcome, Admin!",
        "username": current_user.username,
        "role": current_user.role.name
    }

@app.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(incident_data: IncidentCreate, db: Session=Depends(get_db), current_user: User=Depends(require_roles("L2", "SYSTEM_ADMIN", "ADMIN"))):

    incident = Incident(
        title=incident_data.title.strip(),
        description=incident_data.description.strip(),
        type=incident_data.type,
        priority=incident_data.priority,
        status="NEW",
        created_by_id=current_user.id,
        owner_id = None 
    )

    try:
        db.add(incident)
        db.flush()

        audit = AuditLog(
            incident_id=incident.id,
            actor_id=current_user.id,
            action="INCIDENT_CREATED",
            details="Incident created"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()

    db.refresh(incident)

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

@app.get("/incidents")
def list_incidents(db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    incidents = db.scalars(
        select(Incident).order_by(Incident.created_at.desc())
    ).all()

    result = []

    for incident in incidents:
        owner_data = None 

        if incident.owner is not None:
            owner_data = {
                "id": incident.owner.id,
                "username": incident.owner.username
            }

        result.append({
            "id": incident.id,
            "title": incident.title,
            "type": incident.type,
            "priority": incident.priority,
            "status": incident.status,
            "created_by": {
                "id": incident.created_by_id,
                "username": incident.creator.username
            },
            "owner": owner_data,
            "created_at": incident.created_at
        })

    return result

@app.get("/incidents/{incident_id}")
def get_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    incident = db.scalar(
        select(Incident).options(
            selectinload(Incident.creator),
            selectinload(Incident.owner),
            selectinload(Incident.responders).selectinload(IncidentResponder.user),
            selectinload(Incident.comments).selectinload(Comment.author),
            selectinload(Incident.audit_logs).selectinload(AuditLog.actor)
        ).where(Incident.id == incident_id)
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

    owner_data = None   

    if incident.owner is not None:
        owner_data = {
            "id": incident.owner.id,
            "username": incident.owner.username
        }

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
        "resolved_at": incident.resolved_at
    }

@app.post("/incidents/{incident_id}/claim")
def claim_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles("SYSTEM_ADMIN", "ADMIN"))):

    try:
        statment = (
            update(Incident).where(
                Incident.id == incident_id,
                Incident.owner_id.is_(None),
                Incident.status == "NEW"
            ).values(
                owner_id = current_user.id,
                status="IN_PROGRESS"
            ).returning(
                Incident.id
            )
        )

        claimed_id = db.scalar(statment)

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
            action="INCIDENT_CLAIMED",
            details="Incident claimed by responder"
        )

        db.add(audit)
        db.commit()

    except Exception:
        db.rollback()
        raise   

    return{
        "incident_id": claimed_id,
        "status": "IN_PROGRESS",
        "owner": {  
            "id": current_user.id,
            "username": current_user.username
        },
        "message": "Incident claimed successfully"
    }

@app.post("/incidents/{incident_id}/acknowledge")
def acknowledge_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

        existing_ack = db.scalar(
            select(IncidentAcknowledgement).where(
                IncidentAcknowledgement.incident_id == incident_id,
                IncidentAcknowledgement.user_id == current_user.id
            )
        )

        if existing_ack is not None:
            raise HTTPException(
                status_code=409,
                detail="Incident already acknowledged"
            )

        acknowledgement = IncidentAcknowledgement(
            incident_id = incident_id,
            user_id = current_user.id
        )

        db.add(acknowledgement)
        db.flush()

        audit = AuditLog(
            incident_id=incident_id,
            actor_id=current_user.id,
            action="INCIDENT_ACKNOWLEDGED",
            details="Incident acknowledged by user"
        )

        db.add(audit)
        db.commit()
        db.refresh(acknowledgement)

    except Exception:
        db.rollback()
        raise   

    return {
        "incident_id": incident_id,
        "acknowledged_by": {
            "id": current_user.id,
            "username": current_user.username
        },
        "acknowledged_at" : acknowledgement.acknowledged_at,
        "message": "Incident acknowledged successfully"
    }

