"""Application entry point for the Doomsday Pager API."""

from fastapi import FastAPI  
    
from fastapi.middleware.cors import CORSMiddleware

from routers.auth import router as auth_router
from routers.incidents import router as incidents_router

app = FastAPI(title="Doomsday Pager API")

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

app.include_router(auth_router)
app.include_router(incidents_router)

@app.get("/")
def root():
    return {"message": "Doomsday Pager API is running"}

