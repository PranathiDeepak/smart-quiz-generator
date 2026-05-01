from fastapi import FastAPI

try:
    from quiz_engine import llm
    import_status = "quiz_engine imported successfully"
except Exception as e:
    import_status = f"Import failed: {str(e)}"

app = FastAPI(title="Smart Quiz Generator API")

@app.get("/")
def home():
    return {"message": "Welcome to Smart Quiz Generator API"}

@app.get("/test")
def test():
    return {"status": import_status}