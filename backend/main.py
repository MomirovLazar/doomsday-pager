from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Doomsday Pager API is running"}

