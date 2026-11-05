from fastapi import FastAPI

app = FastAPI(title="AI-Customer-Support")

@app.get("/health")
def health()->dict:
    return {"status":"ok"}
