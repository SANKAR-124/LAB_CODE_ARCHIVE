from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app=FastAPI(title="LabVault Backend API",version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",        # Admin frontend (Vite alternate port)
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message":"Welcome to LabVault"}

@app.get("/health")
def health():
    return {"status":"healthy"}