"""API endpoints for incident management"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from database import get_db
from dependencies import get_current_user, require_roles
from schemas import CommentCreate, IncidentCreate
from constants import IncidentResponse, UserRole
from models import User

from services.incident_service import (
    create_incident_record,
    get_incident_details,
    claim_incident_record,
    respond_to_incident,
    join_incident_record,
    get_incidents_list,
    request_incident_help,
    add_incident_comment,
    resolve_incident_record
)

router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)

@router.post("", status_code=status.HTTP_201_CREATED)
def create_incident(incident_data: IncidentCreate, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.L2, UserRole.SYSTEM_ADMIN, UserRole.ADMIN)),):

    return create_incident_record(
        incident_data=incident_data,
        db=db,
        current_user=current_user,
    )

@router.get("", dependencies=[Depends(get_current_user)],)
def list_incidents(db: Session=Depends(get_db),):

    return get_incidents_list(db)

@router.get("/{incident_id}")
def get_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    return get_incident_details(
        incident_id=incident_id,
        db=db,
        current_user=current_user,
    )

@router.post("/{incident_id}/claim")
def claim_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return claim_incident_record(
        incident_id=incident_id,
        db=db,
        current_user=current_user
    )
    
@router.post("/{incident_id}/acknowledge")
def acknowledge_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return respond_to_incident(
        incident_id=incident_id,
        response=IncidentResponse.ACKNOWLEDGED,
        db=db,
        current_user=current_user
    )

@router.post("/{incident_id}/unavailable")
def unavailable_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return respond_to_incident(
        incident_id=incident_id,
        response=IncidentResponse.UNAVAILABLE,
        db=db,
        current_user=current_user
    )

@router.post("/{incident_id}/join")
def join_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return join_incident_record(
        incident_id=incident_id,
        db=db,
        current_user=current_user,
    )
    
@router.post("/{incident_id}/request-help")
def request_help(incident_id: int, db: Session=Depends(get_db), current_user: User = Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return request_incident_help(
        incident_id=incident_id,
        db=db,
        current_user=current_user,
    )
    
@router.post("/{incident_id}/comments", status_code=status.HTTP_201_CREATED)
def add_comment(incident_id: int, comment_data: CommentCreate, db: Session=Depends(get_db), current_user: User=Depends(get_current_user)):

    return add_incident_comment(
        incident_id=incident_id,
        comment_data=comment_data,
        db=db,
        current_user=current_user
    )
    
@router.post("/{incident_id}/resolve")
def resolve_incident(incident_id: int, db: Session=Depends(get_db), current_user: User=Depends(require_roles(UserRole.SYSTEM_ADMIN, UserRole.ADMIN))):

    return resolve_incident_record(
        incident_id=incident_id,
        db=db,
        current_user=current_user
    )