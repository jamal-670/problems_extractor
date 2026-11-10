# generate_pdf.py
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def compile_blueprint_pdf(doc_data, output_filename: str):
    """
    Takes an architecture JSON/Pydantic object and builds an elegant corporate PDF 
    programmatically using zero token overhead or LLM formatting logic.
    """
    # 1. Setup Document Template Canvas
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        rightMargin=0.75*inch, leftMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # 2. Custom Typography Styling Layouts
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=24, leading=28,
        textColor=colors.HexColor("#1A365D"), # Deep Corporate Navy Blue
        spaceAfter=12
    )
    
    h2_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14, leading=18,
        textColor=colors.HexColor("#2B6CB0"), # Architectural Blue
        spaceBefore=14, spaceAfter=6,
        keepWithNext=True # Prevents orphan headings at bottom of pages
    )
    
    body_style = ParagraphStyle(
        'BodyTextCustom',
        parent=styles['BodyText'],
        fontSize=10, leading=14,
        textColor=colors.HexColor("#2D3748"), # Off-Black text for readability
        spaceAfter=10
    )
    
    bullet_style = ParagraphStyle(
        'BulletCustom',
        parent=body_style,
        leftIndent=15,
        firstLineIndent=-10,
        spaceAfter=6
    )

    # 3. Populate Document Flow Content
    story.append(Paragraph(f"Product Specification: {doc_data.product_name}", title_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Section: Executive Summary
    story.append(Paragraph("1. Executive Summary & Market Pain Point", h2_style))
    story.append(Paragraph(doc_data.executive_summary, body_style))
    
    # Section: Core System Flow
    story.append(Paragraph("2. System Process Operations Pipeline", h2_style))
    for step in doc_data.core_system_flow:
        story.append(Paragraph(f"• {step}", bullet_style))
        
    # Section: Database Schema Design
    story.append(Paragraph("3. Relational Database Entities & Schema Models", h2_style))
    for model in doc_data.database_schema_design:
        story.append(Paragraph(f"• {model}", bullet_style))
        
    # Section: Security and Scaling
    story.append(Paragraph("4. Enterprise Security & Infrastructure Scaling Plan", h2_style))
    story.append(Paragraph(doc_data.security_and_scaling_plan, body_style))

    # 4. Build and Save the actual PDF file cleanly to disk
    doc.build(story)
    print(f"📄 [PDF Compiler] Finished generation. Document successfully saved as: {output_filename}")
