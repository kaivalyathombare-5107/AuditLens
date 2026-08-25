"""
Tamper detection API routes
Location: backend/app/routers/tamper.py
"""

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.ml.tamper_detector import TamperDetector
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.services.audit_service import AuditService

router = APIRouter(prefix="/api/tamper", tags=["tamper"])


class AnalysisResponse(BaseModel):
    document_id: str
    tampered_probability: float
    risk_level: str
    risk_factors: Dict[str, float]
    rule_score: float
    ml_score: float = None
    timestamp: str


class BulkAnalysisRequest(BaseModel):
    document_ids: List[str]


class BulkAnalysisResponse(BaseModel):
    results: Dict[str, AnalysisResponse]
    summary: Dict[str, int]
    timestamp: str


@router.post("/documents/{document_id}/analyze", response_model=AnalysisResponse)
async def analyze_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Analyze a single document for tampering indicators"""
    
    # Verify document exists
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Initialize detector
    detector = TamperDetector(db, model_path="backend/app/ml/tampering_model.pkl")
    
    # Analyze
    result = detector.analyze(document_id)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result["error"])
    
    # Update document in background
    background_tasks.add_task(
        update_document_tampering_status,
        db, document_id, result
    )
    
    # Log analysis
    AuditService.log_action(
        db=db,
        actor_id=doc.uploaded_by,  # Or get from auth
        action="analyze",
        document_id=document_id,
        details={"analysis": result}
    )
    
    return AnalysisResponse(**result)


@router.post("/documents/bulk-analyze", response_model=BulkAnalysisResponse)
async def bulk_analyze_documents(
    request: BulkAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Analyze multiple documents for tampering"""
    
    detector = TamperDetector(db, model_path="backend/app/ml/tampering_model.pkl")
    
    results = {}
    summary = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
    
    for doc_id in request.document_ids:
        try:
            result = detector.analyze(doc_id)
            if "error" not in result:
                results[doc_id] = result
                summary[result["risk_level"]] += 1
        except Exception as e:
            results[doc_id] = {"error": str(e)}
    
    return BulkAnalysisResponse(
        results=results,
        summary=summary,
        timestamp=datetime.utcnow().isoformat()
    )


@router.get("/documents/{document_id}/features")
async def get_tampering_features(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Get extracted tampering features for a document"""
    
    from app.ml.features import FeatureExtractor
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    extractor = FeatureExtractor(db)
    features = extractor.extract_all_features(document_id)
    
    return features


@router.get("/stats")
async def get_tampering_stats(
    db: Session = Depends(get_db)
):
    """Get tampering statistics dashboard"""
    
    from sqlalchemy import func
    
    # Total documents
    total = db.query(Document).count()
    
    # Tampered documents
    tampered = db.query(Document).filter(Document.is_tampered == True).count()
    
    # Risk distribution
    high = db.query(Document).filter(Document.tampering_score >= 70).count()
    medium = db.query(Document).filter(
        Document.tampering_score >= 40,
        Document.tampering_score < 70
    ).count()
    low = db.query(Document).filter(
        Document.tampering_score < 40,
        Document.tampering_score > 0
    ).count()
    
    return {
        "total_documents": total,
        "tampered_documents": tampered,
        "tampering_rate": tampered / total if total > 0 else 0,
        "risk_distribution": {
            "high": high,
            "medium": medium,
            "low": low
        },
        "timestamp": datetime.utcnow().isoformat()
    }


# Background task
async def update_document_tampering_status(db: Session, document_id: str, result: Dict):
    """Update document with tampering analysis results"""
    
    doc = db.query(Document).filter(Document.id == document_id).first()
    if doc:
        doc.is_tampered = result["tampered_probability"] > 0.5
        doc.tampering_score = int(result["tampered_probability"] * 100)
        doc.tampering_metadata = {
            "risk_level": result["risk_level"],
            "risk_factors": result["risk_factors"],
            "rule_score": result["rule_score"],
            "ml_score": result.get("ml_score"),
            "analysis_timestamp": result["timestamp"]
        }
        db.commit()
      
