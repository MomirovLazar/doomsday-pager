from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from auth import authenticate_user
from database import get_db
from schemas import LoginRequest, IncidentCreate

from jwt_handler import create_access_token
from dependencies import get_current_user, require_roles
from models import User, Incident, AuditLog

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