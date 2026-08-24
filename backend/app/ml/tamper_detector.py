"""
Tampering detection engine using rule-based + ML scoring
Location: backend/app/ml/tamper_detector.py
"""

import os
import joblib
import numpy as np
from typing import Dict, Tuple, Optional
from sqlalchemy.orm import Session
import logging

from app.ml.features import FeatureExtractor

logger = logging.getLogger(__name__)


class TamperDetector:
    """Document tampering detection system"""
    
    def __init__(self, db_session: Session, model_path: str = None):
        self.db = db_session
        self.feature_extractor = FeatureExtractor(db_session)
        
        # Rule weights
        self.rule_weights = {
            'hash_changed': 0.30,
            'metadata_mismatch': 0.20,
            'edit_frequency': 0.15,
            'unusual_access_time': 0.15,
            'access_count_spike': 0.10,
            'file_size_delta': 0.10,
        }
        
        # Load ML model if available
        self.model = None
        self.model_scaler = None
        self.feature_columns = None
        
        if model_path and os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                self.model = model_data.get('model')
                self.model_scaler = model_data.get('scaler')
                self.feature_columns = model_data.get('feature_cols')
                logger.info(f"Loaded tampering model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load ML model: {e}")
    
    def analyze(self, document_id: str) -> Dict:
        """Main entry point for document tampering analysis"""
        
        # Extract features
        features = self.feature_extractor.extract_all_features(document_id)
        
        if "error" in features:
            return features
        
        # Calculate rule-based score
        rule_score, risk_factors = self._rule_based_score(features)
        
        # Calculate ML score if available
        ml_score = None
        if self.model:
            ml_score = self._ml_score(features)
        
        # Combine scores (60% rule, 40% ML if available)
        if ml_score is not None:
            final_score = 0.6 * rule_score + 0.4 * ml_score
        else:
            final_score = rule_score
        
        # Determine risk level
        risk_level = self._get_risk_level(final_score)
        
        # Prepare response
        return {
            "document_id": document_id,
            "tampered_probability": round(final_score, 3),
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "rule_score": round(rule_score, 3),
            "ml_score": round(ml_score, 3) if ml_score is not None else None,
            "feature_details": features,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _rule_based_score(self, features: Dict) -> Tuple[float, Dict]:
        """Calculate tampering score using weighted rules"""
        score = 0.0
        risk_factors = {}
        
        for feature, weight in self.rule_weights.items():
            value = features.get(feature, 0)
            if value:
                contribution = weight * min(value, 1.0)
                score += contribution
                risk_factors[feature] = round(contribution, 3)
        
        # Normalize score to 0-1
        score = min(score, 1.0)
        
        return score, risk_factors
    
    def _ml_score(self, features: Dict) -> Optional[float]:
        """Use ML model for scoring"""
        if not self.model:
            return None
        
        try:
            # Prepare feature vector
            feature_vector = self.feature_extractor.prepare_feature_vector(features)
            
            # Scale if scaler available
            if self.model_scaler:
                feature_vector = self.model_scaler.transform(feature_vector)
            
            # Predict probability
            if hasattr(self.model, 'predict_proba'):
                proba = self.model.predict_proba(feature_vector)
                return float(proba[0, 1])  # Probability of tampered
            else:
                return float(self.model.predict(feature_vector)[0])
                
        except Exception as e:
            logger.error(f"ML scoring error: {e}")
            return None
    
    def _get_risk_level(self, score: float) -> str:
        """Convert score to risk level"""
        if score >= 0.7:
            return "HIGH"
        elif score >= 0.4:
            return "MEDIUM"
        else:
            return "LOW"


from datetime import datetime
