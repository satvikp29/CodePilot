from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import review, history
from models.database import init_db

app = FastAPI(title="CodePilot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    init_db()

app.include_router(review.router, prefix="/api")
app.include_router(history.router, prefix="/api")

@app.get("/health")
def health():
    return {"status": "ok", "service": "CodePilot API"}
