from fastapi import FastAPI
import uvicorn
import json

app = FastAPI(title="Health API", version="1.0.0")

@app.get("/health")
def health():
    return {"status": "OK"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
