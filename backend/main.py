from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from auth import authenticate_user
from database import get_db
from schemas import LoginRequest

from jwt_handler import create_access_token
from dependencies import get_current_user
from models import User

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

