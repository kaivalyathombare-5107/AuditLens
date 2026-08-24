"""
Feature extraction for document tampering detection
Location: backend/app/ml/features.py
"""

import os
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from sqlalchemy.orm import Session
import pandas as pd
import numpy as np

from app.models.document import Document
from app.models.audit_log import AuditLog
from app.models.document_access import DocumentAccess
from app.services.hash_service import HashService


class FeatureExtractor:
    """Extract tampering-related features from document and metadata"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.hash_service = HashService()
    
    def extract_all_features(self, document_id: str) -> Dict[str, Any]:
        """Extract all tampering features for a document"""
        
        # Get document
        doc = self.db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            return {"error": "Document not found"}
        
        features = {
            'document_id': str(doc.id),
            'file_size_delta': 0.0,
            'metadata_mismatch': 0,
            'edit_frequency': 0,
            'unusual_access_time': 0,
            'hash_changed': 0,
            'access_count_spike': 0,
            'file_age_days': 0,
            'structure_anomaly_score': 0,
            'text_entropy': 0,
            'text_length': 0,
        }
        
        # 1. Check if hash changed
        features['hash_changed'] = self._check_hash_changed(doc)
        
        # 2. Analyze audit logs
        audit_features = self._extract_audit_features(doc.id)
        features.update(audit_features)
        
        # 3. Check metadata mismatch
        features['metadata_mismatch'] = self._check_metadata_mismatch(doc)
        
        # 4. File size delta
        features['file_size_delta'] = self._calculate_file_size_delta(doc)
        
        # 5. File age
        features['file_age_days'] = (datetime.utcnow() - doc.created_at).days
        
        # 6. Text-based features (if text available)
        text_features = self._extract_text_features(doc)
        features.update(text_features)
        
        return features
    
    def _check_hash_changed(self, doc: Document) -> int:
        """Check if current file hash matches stored hash"""
        try:
            current_hash = self.hash_service.compute_file_hash(doc.file_path)
            if current_hash and current_hash != doc.file_hash:
                return 1
        except Exception:
            pass
        return 0
    
    def _extract_audit_features(self, document_id: str) -> Dict:
        """Extract features from audit logs"""
        features = {
            'edit_frequency': 0,
            'unusual_access_time': 0,
            'access_count_spike': 0,
        }
        
        # Get all logs for this document
        logs = self.db.query(AuditLog).filter(
            AuditLog.document_id == document_id
        ).order_by(AuditLog.timestamp).all()
        
        if not logs:
            return features
        
        # Edit frequency (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        recent_edits = [l for l in logs if l.action == 'edit' and l.timestamp > thirty_days_ago]
        features['edit_frequency'] = len(recent_edits)
        
        # Unusual access time (10 PM - 6 AM)
        night_access = [
            l for l in logs 
            if 22 <= l.timestamp.hour or l.timestamp.hour < 6
        ]
        features['unusual_access_time'] = 1 if night_access else 0
        
        # Access count spike (last 24h vs 7-day avg)
        last_24h = [l for l in logs if l.timestamp > datetime.utcnow() - timedelta(hours=24)]
        last_7d = [l for l in logs if l.timestamp > datetime.utcnow() - timedelta(days=7)]
        
        daily_avg = len(last_7d) / 7.0 if last_7d else 0
        if daily_avg > 0:
            spike_ratio = len(last_24h) / daily_avg
            features['access_count_spike'] = 1 if spike_ratio > 3 else 0
        
        return features
    
    def _check_metadata_mismatch(self, doc: Document) -> int:
        """Check for metadata inconsistencies"""
        mismatch_count = 0
        
        try:
            stat = os.stat(doc.file_path)
            
            # Check if modified before created
            if stat.st_mtime < stat.st_ctime:
                mismatch_count += 1
            
            # Check if modified very recently (within 60 seconds of upload)
            if abs(stat.st_mtime - doc.created_at.timestamp()) < 60:
                mismatch_count += 1
            
            # Check if file was accessed but not modified
            if stat.st_atime > stat.st_mtime and doc.version > 1:
                mismatch_count += 1
                
        except Exception:
            pass
        
        return 1 if mismatch_count > 0 else 0
    
    def _calculate_file_size_delta(self, doc: Document) -> float:
        """Calculate file size change compared to previous version"""
        try:
            if doc.version <= 1:
                return 0.0
            
            # Find previous version
            prev_version = self.db.query(Document).filter(
                Document.case_id == doc.case_id,
                Document.version == doc.version - 1
            ).first()
            
            if not prev_version:
                return 0.0
            
            current_size = os.path.getsize(doc.file_path)
            prev_size = os.path.getsize(prev_version.file_path)
            
            if prev_size > 0:
                delta = abs(current_size - prev_size) / prev_size
                return min(delta, 1.0)  # Cap at 1.0
            
        except Exception:
            pass
        
        return 0.0
    
    def _extract_text_features(self, doc: Document) -> Dict:
        """Extract text-based features"""
        features = {
            'text_entropy': 0.0,
            'text_length': 0,
            'structure_anomaly_score': 0.0,
        }
        
        try:
            # Try to load text from document metadata
            if doc.tampering_metadata and 'extracted_text' in doc.tampering_metadata:
                text = doc.tampering_metadata['extracted_text']
                features['text_length'] = len(text)
                
                if text:
                    features['text_entropy'] = self._calculate_entropy(text)
                    features['structure_anomaly_score'] = self._detect_structure_anomalies(text)
                    
        except Exception:
            pass
        
        return features
    
    def _calculate_entropy(self, text: str) -> float:
        """Calculate Shannon entropy of text"""
        from collections import Counter
        import math
        
        if not text:
            return 0.0
        
        freq = Counter(text)
        text_length = len(text)
        entropy = 0.0
        
        for count in freq.values():
            p = count / text_length
            entropy -= p * math.log2(p)
        
        return min(entropy / 10.0, 1.0)  # Normalize
    
    def _detect_structure_anomalies(self, text: str) -> float:
        """Detect structural anomalies in text"""
        import re
        
        anomaly_score = 0.0
        
        if not text or len(text) < 100:
            return 0.0
        
        # Check for unusual character frequency
        special_chars = len(re.findall(r'[^a-zA-Z0-9\s]', text)) / len(text)
        if special_chars > 0.3:
            anomaly_score += 0.3
        
        # Check for repeated patterns
        sentences = re.split(r'[.!?]+', text)
        from collections import Counter
        if len(sentences) > 10:
            sentence_counter = Counter([s.strip().lower() for s in sentences if len(s) > 20])
            repeated = [s for s, count in sentence_counter.items() if count > 3]
            if repeated:
                anomaly_score += 0.3
        
        # Check for inconsistent date formats
        us_dates = len(re.findall(r'\d{1,2}/\d{1,2}/\d{4}', text))
        uk_dates = len(re.findall(r'\d{1,2}-\d{1,2}-\d{4}', text))
        if us_dates > 0 and uk_dates > 0:
            anomaly_score += 0.2
        
        return min(anomaly_score, 1.0)
    
    def prepare_feature_vector(self, features: Dict) -> np.ndarray:
        """Convert features dict to numpy array for model prediction"""
        feature_keys = [
            'file_size_delta',
            'metadata_mismatch',
            'edit_frequency',
            'unusual_access_time',
            'hash_changed',
            'access_count_spike',
            'file_age_days',
            'structure_anomaly_score',
            'text_entropy',
            'text_length'
        ]
        
        # Scale text_length to 0-1 range (assuming max 10000 chars)
        if features.get('text_length', 0) > 10000:
            features['text_length'] = 1.0
        else:
            features['text_length'] = features.get('text_length', 0) / 10000.0
        
        vector = np.array([[
            features.get(key, 0) for key in feature_keys
        ]])
        
        return vector
