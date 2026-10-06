from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session

from auth import authenticate_user
from database import get_db
from schemas import LoginRequest

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
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invaild username or password"
        )

    return {
        "message": "Login succsessful",
        "username": user.username
    }

