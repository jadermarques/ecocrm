from fastapi import FastAPI
import os

app = FastAPI(title="ECOCRM Platform API")

@app.get("/")
def read_root():
    return {"message": "Welcome to ECOCRM Platform API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "env": os.getenv("APP_ENV")}
