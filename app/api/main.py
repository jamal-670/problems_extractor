# app/api/main.py
import sys
import os
import json
import io
import asyncio
from datetime import timedelta
from fastapi import FastAPI, BackgroundTasks, HTTPException, Depends, status, Request
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import jwt
from dotenv import load_dotenv

# Load environmental variables securely
load_dotenv()

from app.scraper import RedditScraper, UpworkScraper, LootDropScraper, RazorpayScraper, YCScraper
from app.engine.processor import generate_agent_blueprint
from app.database import init_db, save_blueprint_to_db, SessionLocal, SavedBlueprint, User
from app.database.auth import get_password_hash, verify_password, create_access_token, SECRET_KEY, ALGORITHM

from app.agents import SoftwareArchitectureDoc, client as instructor_client, compile_blueprint_pdf

app = FastAPI(
    title="ProblemRadar AI Secure Core Engine", 
    version="1.1.0",
    redirect_slashes=False
)

# Security entrypoint declaration
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

@app.on_event("startup")
def on_startup():
    init_db()

class UserRegister(BaseModel):
    username: str
    password: str

class ScanRequest(BaseModel):
    niche: str
    limit_per_source: int = 3

# --- UNIVERSAL GUARD FUNCTION ---
def verify_raw_token(token: str) -> str:
    """Decodes and validates a raw JWT token string."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate access credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        return username
    except jwt.PyJWTError:
        raise credentials_exception

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    """Dependency guard used for simple GET endpoints."""
    return verify_raw_token(token)

# --- AUTH ENDPOINTS ---
@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister):
    db = SessionLocal()
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        db.close()
        raise HTTPException(status_code=400, detail="Username already registered.")
    
    new_user = User(username=user_data.username, hashed_password=get_password_hash(user_data.password))
    db.add(new_user)
    db.commit()
    db.close()
    return {"message": "User registered successfully."}

@app.post("/api/v1/auth/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    db = SessionLocal()
    user = db.query(User).filter(User.username == form_data.username).first()
    db.close()
    
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- SYSTEM ENGINE ROUTE TASKS ---
def background_discovery_drop(niche: str, limit: int):
    print(f"🚀 [Background Task] Deploying scraping fleet for: '{niche}'")
    fleet = [RedditScraper(), UpworkScraper(), LootDropScraper(), RazorpayScraper(), YCScraper()]
    for scraper in fleet:
        try:
            raw_data = asyncio.run(scraper.scrape(target_niche=niche, max_results=limit))
            for item in raw_data:
                try:
                    blueprint = generate_agent_blueprint(item["text"])
                    save_blueprint_to_db(source_url=item["url"], blueprint_data=blueprint)
                except ValueError:
                    continue
                except Exception as e:
                    print(f"⚠️ Error processing row: {e}")
        except Exception as e:
            print(f"❌ Scraper failure: {e}")

# --- PROTECTED ENDPOINTS ---

@app.post("/api/v1/scan")
def trigger_niche_scan(payload: ScanRequest, background_tasks: BackgroundTasks, request: Request):
    """
    SECURE: Reads authorization packets directly out of the raw incoming HTTP stream.
    This completely eliminates 401 dependency injection conflicts on POST routes.
    """
    auth_header = request.headers.get("Authorization")
    header_parts = auth_header.split(" ") if auth_header else []
    safe_auth_header = (
        f"{header_parts[0]} [REDACTED]"
        if len(header_parts) > 1
        else "[REDACTED]" if auth_header else None
    )
    print(f"DEBUG: Raw Header Received -> {safe_auth_header}")
    safe_split_result = (
        [header_parts[0], *("[REDACTED]" for _ in header_parts[1:])]
        if header_parts else "None"
    )
    print(f"DEBUG: Split List Result -> {safe_split_result}")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or malformed Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract index 1 safely to grab only the raw string token from the 'Bearer <token>' split
    token = auth_header.split(" ")[1]
    current_user = verify_raw_token(token)
    
    # Hand off execution task loop to background workers cleanly
    background_tasks.add_task(background_discovery_drop, payload.niche, payload.limit_per_source)
    return {"status": "processing", "user": current_user, "message": "Scraping background fleet deployed."}

@app.get("/api/v1/blueprints")
def get_all_blueprints(current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    try:
        records = db.query(SavedBlueprint).order_by(SavedBlueprint.created_at.desc()).all()
        results = []
        for r in records:
            results.append({
                "id": r.id,
                "source_url": r.source_url,
                "target_industry": r.target_industry,
                "validated_problem": r.validated_problem,
                "required_backend_stack": json.loads(r.required_backend_stack),
                "database_entities": json.loads(r.database_entities),
                "critical_api_endpoints": json.loads(r.critical_api_endpoints)
            })
        return results
    finally:
        db.close()

@app.get("/api/v1/blueprints/{blueprint_id}/download")
def download_blueprint_pdf(blueprint_id: int, current_user: str = Depends(get_current_user)):
    db = SessionLocal()
    blueprint = db.query(SavedBlueprint).filter(SavedBlueprint.id == blueprint_id).first()
    db.close()

    if not blueprint:
        raise HTTPException(status_code=404, detail="Specification record not found.")

    try:
        doc_specification = instructor_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            response_model=SoftwareArchitectureDoc,
            messages=[
                {"role": "system", "content": "You are a Principal Enterprise Systems Architect."},
                {"role": "user", "content": f"Create specs document layout for: {blueprint.validated_problem}"}
            ],
            temperature=0.2
        )

        pdf_buffer = io.BytesIO()
        compile_blueprint_pdf(doc_specification, pdf_buffer)
        pdf_buffer.seek(0)

        return StreamingResponse(
            pdf_buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=Architecture_{blueprint_id}.pdf"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")
