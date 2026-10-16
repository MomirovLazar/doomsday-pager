from fastapi import (
    Depends, 
    FastAPI, 
    HTTPException, 
    status
)

from fastapi.middleware.cors import CORSMiddleware

from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from auth import authenticate_user
from database import get_db

from schemas import (
    LoginRequest, 
    IncidentCreate,
    CommentCreate
)

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

from constants import (
    IncidentStatus,
    IncidentResponse,
    UserRole,
    AuditAction
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware, 
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
    current_user: User = Depends(require_roles(UserRole.ADMIN))
):
    return {
        "message": "Welcome, Admin!",
        "username": current_user.username,
        "role": current_user.role.name
    }

@app.post("/incidents", status_code=status.HTTP_201_CREATED)
def create_incident(incident_data: IncidentCreate, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.L2, UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

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

    my_response = None

    for item in response_data:
        if item["user"]["id"] == current_user.id:
            my_response = item["response"]
            break

    help_requested = False

    for event in incident.audit_logs:
        if event.action == AuditAction.HELP_REQUESTED:
            help_requested = True
            break

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

@app.post("/incidents/{incident_id}/claim")
def claim_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    try:
        statment = (
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

@app.post("/incidents/{incident_id}/acknowledge")
def acknowledge_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    return respond_to_incident(
        incident_id=incident_id,
        response=IncidentResponse.ACKNOWLEDGED,
        db=db,
        current_user=current_user
    )

@app.post("/incidents/{incident_id}/unavailable")
def unavailable_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    return respond_to_incident(
        incident_id=incident_id,
        response=IncidentResponse.UNAVAILABLE,
        db=db,
        current_user=current_user
    )

@app.post("/incidents/{incident_id}/join")
def join_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    try:
        incident = db.get(Incident, incident_id)

        if incident is None:
            raise HTTPException(
                status_code=404, 
                detail="Incident not found"
            )

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

@app.post("/incidents/{incident_id}/request-help")
def request_help(incident_id: int, db: Session=Depends(get_db), current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    try:
        incident = db.scalar(
            select(Incident).where(Incident.id == incident_id).with_for_update()
        )

        if incident is None:
            raise HTTPException(
                status_code=404, 
                detail="Incident not found"
            )

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

@app.post("/incidents/{incident_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(incident_id: int, comment_data: CommentCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

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

@app.post("/incidents/{incident_id}/resolve")
def resolve_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    try:
        incident = db.scalar(
            select(Incident).where(Incident.id == incident_id).with_for_update()
        )

        if incident is None:
            raise HTTPException(
                status_code=404,
                detail="Incident not found"
            )

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
        db.refresh(audit)

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