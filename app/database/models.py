# app/database/models.py
import json
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Initialize SQLite Database Engine coordinates
DATABASE_URL = "sqlite:///problem_radar.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 2. Existing Blueprint Table Layout Model Profile
class SavedBlueprint(Base):
    __tablename__ = "saved_blueprints"

    id = Column(Integer, primary_key=True, index=True)
    source_url = Column(String, nullable=False)
    target_industry = Column(String, index=True)
    validated_problem = Column(Text, nullable=False)
    required_backend_stack = Column(Text, nullable=False) 
    database_entities = Column(Text, nullable=False)
    critical_api_endpoints = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3. New User Authentication Security Profile (This was missing!)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 4. Helper utilities to initialize files layout systems
def init_db():
    Base.metadata.create_all(bind=engine)

def save_blueprint_to_db(source_url: str, blueprint_data) -> None:
    db = SessionLocal()
    try:
        new_record = SavedBlueprint(
            source_url=source_url,
            target_industry=blueprint_data.target_industry,
            validated_problem=blueprint_data.validated_problem,
            required_backend_stack=json.dumps(blueprint_data.required_backend_stack),
            database_entities=json.dumps(blueprint_data.database_entities),
            critical_api_endpoints=json.dumps(blueprint_data.critical_api_endpoints)
        )
        db.add(new_record)
        db.commit()
        print(f"💾 [Database] Saved spec profile for: {blueprint_data.target_industry}")
    except Exception as e:
        db.rollback()
        print(f"❌ [Database Error] Commit failure: {e}")
    finally:
        db.close()
