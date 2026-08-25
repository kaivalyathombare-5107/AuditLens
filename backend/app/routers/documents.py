"""
Document management API routes (updated with tamper detection)
Location: backend/app/routers/documents.py
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import Optional
import os
import shutil
from datetime import datetime

from app.database import get_db
from app.models.document import Document
from app.models.case import Case
from app.models.audit_log import AuditLog
from app.ml.predictor import DocumentPredictor
from app.ml.tamper_detector import TamperDetector
from app.services.hash_service import HashService
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Initialize services
hash_service = HashService()
predictor = DocumentPredictor(model_path="backend/app/ml/model.pkl")


@router.post("/upload")
async def upload_document(
    case_id: str = Form(...),
    file: UploadFile = File(...),
    uploaded_by: str = Form(...),
    db: Session = Depends(get_db)
):
    """Upload a document with classification and tampering analysis"""
    
    # Verify case exists
    case = db.query(Case).filter(Case.id == case_id).first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    
    # Save file
    upload_dir = f"uploads/case_{case_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Compute hash
    file_hash = hash_service.compute_file_hash(file_path)
    
    # Check for duplicates
    existing = db.query(Document).filter(
        Document.case_id == case_id,
        Document.file_hash == file_hash
    ).first()
    
    if existing:
        os.remove(file_path)
        raise HTTPException(
            status_code=400,
            detail=f"Duplicate document found: {existing.file_name} (version {existing.version})"
        )
    
    # Extract text and classify
    text = extract_text_from_file(file_path)
    classification = predictor.classify(text) if text else {"category": "Other", "confidence": 0.0}
    
    # Create document record
    doc = Document(
        case_id=case_id,
        doc_type=classification.get("category", "Other"),
        file_name=file.filename,
        file_path=file_path,
        file_hash=file_hash,
        version=1,
        uploaded_by=uploaded_by,
        created_at=datetime.utcnow()
    )
    
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Run tampering analysis
    tamper_detector = TamperDetector(db)
    tamper_result = tamper_detector.analyze(str(doc.id))
    
    # Log upload
    AuditService.log_action(
        db=db,
        actor_id=uploaded_by,
        action="upload",
        document_id=doc.id,
        details={
            "filename": file.filename,
            "classification": classification,
            "tampering": tamper_result
        }
    )
    
    return {
        "document": {
            "id": str(doc.id),
            "file_name": doc.file_name,
            "doc_type": doc.doc_type,
            "version": doc.version,
            "uploaded_at": doc.created_at.isoformat()
        },
        "classification": classification,
        "tampering": tamper_result
    }


@router.get("/{document_id}/analyze")
async def analyze_document_tampering(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Analyze document for tampering (on-demand)"""
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    detector = TamperDetector(db)
    result = detector.analyze(document_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    return result


def extract_text_from_file(file_path: str) -> str:
    """Extract text from file (simple version)"""
    # This is a placeholder - use ocr_utils in production
    try:
        if file_path.lower().endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif file_path.lower().endswith('.pdf'):
            # Use your existing ocr_utils here
            return "Extracted PDF text"
    except Exception:
        pass
    return ""
