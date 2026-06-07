from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_db
from app.api import auth, chat
import os

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI Legal Assistant for Indian Legal System"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(chat.router)


@app.on_event("startup")
def startup_event():
    """Initialize database and seed sample data on startup."""
    init_db()
    
    # Automatically seed default demo user if not exists
    from app.db.session import SessionLocal
    from app.models.database import User
    from app.core.auth import get_password_hash
    
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.username == "demo").first()
        if not existing_user:
            demo_user = User(
                username="demo",
                hashed_password=get_password_hash("demo123")
            )
            db.add(demo_user)
            db.commit()
            print("[SUCCESS] In-memory database seeded with default user 'demo' (password: 'demo123')")
    except Exception as e:
        print(f"[ERROR] Failed to seed in-memory database: {e}")
        db.rollback()
    finally:
        db.close()


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0",port=os.environ.get("PORT", 10000))
