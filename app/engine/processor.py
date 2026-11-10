# app/engine/processor.py
import os
from typing import List
from pydantic import BaseModel, Field
import instructor
from groq import Groq 

# The definitive universal data shape needed by an execution agent
class AgentReadySpecification(BaseModel):
    target_industry: str = Field(description="The market sector (e.g., Logistics, FinTech, Legal Tech).")
    validated_problem: str = Field(description="The core bottleneck or expensive manual task being faced.")
    required_backend_stack: List[str] = Field(description="Specific technical layers the agent must build (e.g., FastAPI, Celery Async Queue, PGVector, PyPDF).")
    database_entities: List[str] = Field(description="The primary data tables/models needed (e.g., User, Invoice, AuditLog, ProcessingJob).")
    critical_api_endpoints: List[str] = Field(description="List of core API routes for the backend (e.g., POST /v1/upload, GET /v1/status).")

# Initialize the cost-optimized pipeline client
# Using llama-3.1-8b-instant keeps token extraction incredibly inexpensive
client = instructor.from_groq(Groq(api_key=os.environ.get("GROQ_API_KEY")))

def clean_and_validate_text(raw_text: str) -> bool:
    """Deterministic heuristic filter to use less LLM tokens."""
    if len(raw_text.strip()) < 100:
        return False
        
    problem_signals = ["manual", "waste", "excel", "sheet", "hourly", "broken", "dislike", "failed", "clunky", "error"]
    text_lower = raw_text.lower()
    
    # Only allow the text to proceed if it exhibits authentic pain signals
    return any(signal in text_lower for signal in problem_signals)

def generate_agent_blueprint(raw_text: str) -> AgentReadySpecification:
    """The Universal Parser Prompt."""
    
    # 1. First run the deterministic code guardrail to prevent wasteful API calls
    if not clean_and_validate_text(raw_text):
        raise ValueError("Text did not pass the deterministic pain-signal pre-filter.")

    # 2. Universal Prompt focused purely on generating code-agent specifications
    universal_prompt = (
        "You are an enterprise system architect parsing unstructured market raw data. "
        "Analyze the user text and map it directly into the strict technical schema provided. "
        "Focus heavily on the backend architecture, data pipelines, and data models required "
        "so that a junior engineer or an autonomous code agent can build this micro-service instantly.\n\n"
        f"SOURCE TEXT TO EXTRACT:\n{raw_text}"
    )

    blueprint = client.chat.completions.create(
        model="llama-3.1-8b-instant", # Cost-effective model optimized for JSON/Function tool calling
        response_model=AgentReadySpecification,
        messages=[
            {"role": "user", "content": universal_prompt}
        ],
        temperature=0.1 # Low temperature ensures strict, non-creative, programmatic JSON formatting
    )
    return blueprint
