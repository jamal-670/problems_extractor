# agent.py
import os
import json
from pydantic import BaseModel, Field
from typing import List
import instructor
from groq import Groq 
from app.database import SessionLocal, SavedBlueprint
from .generate_pdf import compile_blueprint_pdf
from dotenv import load_dotenv

# Automatically searches for and loads local .env variables into operating system memory maps
load_dotenv() 
 # We will build this in Step 3

# 1. Define the rigorous documentation layout schema we want the AI to output
class SoftwareArchitectureDoc(BaseModel):
    product_name: str = Field(description="A strategic name for the micro-SaaS application.")
    executive_summary: str = Field(description="A thorough breakdown of the market pain point and targeted user persona.")
    database_schema_design: List[str] = Field(description="Detailed SQL columns, types, and relationships.")
    core_system_flow: List[str] = Field(description="Step-by-step description of data input, processing, and output pipelines.")
    security_and_scaling_plan: str = Field(description="How to protect customer data, manage concurrency, and optimize database indexing.")

# Initialize the schema-enforced Instructor client
client = instructor.from_groq(Groq(api_key=os.environ.get("GROQ_API_KEY")))

def run_documentation_agent():
    db = SessionLocal()
    # Pull the latest structured entry from your SQLite data drop
    blueprint = db.query(SavedBlueprint).order_by(SavedBlueprint.id.desc()).first()
    db.close()
    
    if not blueprint:
        print("📭 No blueprints found in the database. Run a system scan first!")
        return

    print(f"🤖 [Agent] Compiling deep system architecture specifications into JSON...")

    # 2. Extract structured documentation text parameters
    doc_specification = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # Using a robust model for comprehensive enterprise architectural depth
        response_model=SoftwareArchitectureDoc,
        messages=[
            {
                "role": "system", 
                "content": "You are a Principal Enterprise Systems Architect. You output exhaustive, precise technical specifications."
            },
            {
                "role": "user", 
                "content": (
                    f"Create an exhaustive, professional software engineering design document for this target architecture:\n\n"
                    f"Industry: {blueprint.target_industry}\n"
                    f"Core Bottleneck: {blueprint.validated_problem}\n"
                    f"Stack: {blueprint.required_backend_stack}\n"
                    f"Endpoints: {blueprint.critical_api_endpoints}"
                )
            }
        ],
        temperature=0.2
    )

    # 3. Hand over the pristine JSON object directly to your own native PDF engine!
    pdf_filename = f"System_Architecture_{blueprint.id}.pdf"
    compile_blueprint_pdf(doc_specification, pdf_filename)

if __name__ == "__main__":
    run_documentation_agent()
