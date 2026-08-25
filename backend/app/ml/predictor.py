"""
Document classifier using XGBoost + Tampering detection
Location: backend/app/ml/predictor.py
"""

import os
import joblib
import pandas as pd
import numpy as np
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DocumentPredictor:
    """Document classification and tampering detection"""
    
    def __init__(self, model_path: str = None, tamper_model_path: str = None):
        self.classifier = None
        self.vectorizer = None
        self.label_encoder = None
        
        # Load classification model
        if model_path and os.path.exists(model_path):
            try:
                model_data = joblib.load(model_path)
                self.classifier = model_data.get('model')
                self.vectorizer = model_data.get('vectorizer')
                self.label_encoder = model_data.get('label_encoder')
                logger.info(f"Loaded classification model from {model_path}")
            except Exception as e:
                logger.warning(f"Could not load classification model: {e}")
    
    def classify(self, text: str) -> Dict:
        """Classify document text into category"""
        if not self.classifier or not self.vectorizer:
            return {
                "category": "Other",
                "confidence": 0.0,
                "error": "Model not loaded"
            }
        
        try:
            # Vectorize text
            text_vector = self.vectorizer.transform([text])
            
            # Predict
            prediction = self.classifier.predict(text_vector)
            probabilities = self.classifier.predict_proba(text_vector)
            
            # Get category and confidence
            category = self.label_encoder.inverse_transform(prediction)[0]
            confidence = float(max(probabilities[0]))
            
            # Get top 3 predictions
            top_indices = np.argsort(probabilities[0])[-3:][::-1]
            top_predictions = [
                {
                    "category": self.label_encoder.inverse_transform([idx])[0],
                    "confidence": float(probabilities[0][idx])
                }
                for idx in top_indices
            ]
            
            return {
                "category": category,
                "confidence": confidence,
                "top_predictions": top_predictions,
                "needs_review": confidence < 0.75
            }
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                "category": "Other",
                "confidence": 0.0,
                "error": str(e)
            }
