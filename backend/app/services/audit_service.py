"""
Audit logging service
Location: backend/app/services/audit_service.py
"""

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
import json

from app.models.audit_log import AuditLog


class AuditService:
    """Service for writing audit logs"""
    
    @staticmethod
    def log_action(
        db: Session,
        actor_id: str,
        action: str,
        document_id: Optional[str] = None,
        case_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ) -> AuditLog:
        """Log an action to the audit trail"""
        
        audit_log = AuditLog(
            actor_id=actor_id,
            action=action,
            document_id=document_id,
            case_id=case_id,
            timestamp=datetime.utcnow(),
            ip_address=ip_address,
            details=details or {}
        )
        
        db.add(audit_log)
        db.commit()
        db.refresh(audit_log)
        
        return audit_log
    
    @staticmethod
    def get_document_audit_trail(
        db: Session,
        document_id: str,
        limit: int = 100
    ) -> list:
        """Get audit trail for a document"""
        
        return db.query(AuditLog).filter(
            AuditLog.document_id == document_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit).all()
