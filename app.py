from fastapi import FastAPI

app = FastAPI(title="Smart Quiz Generator API")

@app.get("/")
def home():
    return {"message": "Welcome to Smart Quiz Generator API"}

@app.get("/test")
def test():
    return {"status": "working"}