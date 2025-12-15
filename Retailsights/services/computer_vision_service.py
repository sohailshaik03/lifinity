"""
Computer Vision Service
AI-powered visual inspection, shelf monitoring, and automated quality control.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
import base64
from io import BytesIO
from sqlalchemy import text
from ..db import get_session
from ..models import Product
from ..logger import logger

try:
    from PIL import Image
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False
    logger.warning("PIL/numpy not available for computer vision")


class ComputerVisionService:
    """AI-powered visual inspection and monitoring."""
    
    @staticmethod
    def detect_product_freshness(image_data: bytes, product_type: str) -> Dict[str, Any]:
        """
        Analyze product image to detect freshness/quality.
        Uses AI to detect:
        - Discoloration
        - Mold/spoilage
        - Damaged packaging
        - Freshness score (0-100)
        """
        if not CV_AVAILABLE:
            return {
                "error": "Computer vision libraries not available",
                "note": "Install Pillow and numpy for CV features"
            }
        
        try:
            # Load image
            image = Image.open(BytesIO(image_data))
            img_array = np.array(image)
            
            # Simulate AI analysis (in production, use trained ML model)
            # This would use TensorFlow/PyTorch model trained on food images
            
            height, width = img_array.shape[:2]
            
            # Simple heuristics for demo
            # In production: Use pretrained models like ResNet, EfficientNet
            avg_brightness = np.mean(img_array)
            color_variance = np.std(img_array)
            
            # Freshness score based on image properties
            freshness_score = min(100, max(0, 
                85 + (avg_brightness / 255 * 10) - (color_variance / 10)
            ))
            
            quality_indicators = {
                "discoloration_detected": color_variance > 60,
                "dark_spots_count": int(np.sum(img_array < 50) / 1000),
                "brightness_score": round(avg_brightness / 255 * 100, 1),
                "color_uniformity": round(100 - (color_variance / 128 * 100), 1)
            }
            
            # Determine quality grade
            if freshness_score >= 85:
                grade = "EXCELLENT"
                recommendation = "Sell at full price"
            elif freshness_score >= 70:
                grade = "GOOD"
                recommendation = "Sell at full price or minor discount"
            elif freshness_score >= 50:
                grade = "FAIR"
                recommendation = "Apply 30-50% discount immediately"
            else:
                grade = "POOR"
                recommendation = "Remove from shelf - potential waste"
            
            return {
                "success": True,
                "freshness_score": round(freshness_score, 1),
                "quality_grade": grade,
                "indicators": quality_indicators,
                "recommendation": recommendation,
                "product_type": product_type,
                "image_size": f"{width}x{height}",
                "analyzed_at": datetime.now().isoformat(),
                "model_version": "CV-Demo-v1.0"
            }
            
        except Exception as e:
            logger.error(f"detect_product_freshness error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def detect_shelf_compliance(image_data: bytes, expected_layout: Dict) -> Dict[str, Any]:
        """
        Check if shelf is stocked correctly.
        - Products in correct position
        - No gaps
        - Facing labels visible
        - FIFO compliance (oldest at front)
        """
        if not CV_AVAILABLE:
            return {"error": "Computer vision not available"}
        
        try:
            image = Image.open(BytesIO(image_data))
            img_array = np.array(image)
            
            # Simulate shelf analysis
            # In production: Use object detection (YOLO, Faster R-CNN)
            
            height, width = img_array.shape[:2]
            
            # Detect empty spaces (dark regions)
            gray = np.mean(img_array, axis=2)
            empty_percentage = np.sum(gray < 80) / gray.size * 100
            
            # Detect product count (simplified)
            # In production: Use object detection to count products
            estimated_products = int((100 - empty_percentage) / 10)
            
            compliance_score = 100 - empty_percentage
            
            issues = []
            if empty_percentage > 20:
                issues.append({
                    "type": "LOW_STOCK",
                    "severity": "MEDIUM",
                    "message": f"{empty_percentage:.0f}% shelf space empty"
                })
            
            if empty_percentage > 50:
                issues.append({
                    "type": "OUT_OF_STOCK",
                    "severity": "HIGH",
                    "message": "Critical: Shelf more than 50% empty"
                })
            
            return {
                "success": True,
                "compliance_score": round(compliance_score, 1),
                "shelf_fullness": round(100 - empty_percentage, 1),
                "estimated_products": estimated_products,
                "issues": issues,
                "recommendation": "Restock immediately" if empty_percentage > 50 else "Monitor stock levels",
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"detect_shelf_compliance error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def detect_damaged_packaging(image_data: bytes) -> Dict[str, Any]:
        """
        Detect damaged, torn, or opened packaging.
        Critical for food safety and waste prevention.
        """
        if not CV_AVAILABLE:
            return {"error": "Computer vision not available"}
        
        try:
            image = Image.open(BytesIO(image_data))
            img_array = np.array(image)
            
            # Simulate damage detection
            # In production: Use CNN trained on damaged packaging images
            
            # Edge detection for tears/damage
            # Simplified: Check for high contrast edges
            edges = np.abs(np.diff(img_array.astype(float), axis=0))
            edge_intensity = np.mean(edges)
            
            # Color consistency (damage usually causes color variation)
            color_std = np.std(img_array)
            
            # Damage score
            damage_score = min(100, (edge_intensity / 10 + color_std / 2))
            
            is_damaged = damage_score > 40
            
            damage_types = []
            if edge_intensity > 30:
                damage_types.append("TORN_EDGES")
            if color_std > 50:
                damage_types.append("DISCOLORATION")
            if damage_score > 60:
                damage_types.append("SEVERE_DAMAGE")
            
            return {
                "success": True,
                "is_damaged": is_damaged,
                "damage_score": round(damage_score, 1),
                "damage_types": damage_types,
                "confidence": round(min(95, 60 + damage_score / 3), 1),
                "recommendation": "Remove from shelf" if is_damaged else "Packaging intact",
                "analyzed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"detect_damaged_packaging error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def count_products_on_shelf(image_data: bytes, product_category: str) -> Dict[str, Any]:
        """
        Automated stock counting using computer vision.
        Eliminates manual counting.
        """
        if not CV_AVAILABLE:
            return {"error": "Computer vision not available"}
        
        try:
            image = Image.open(BytesIO(image_data))
            img_array = np.array(image)
            
            # Simulate product counting
            # In production: Use YOLO or Faster R-CNN for object detection
            
            height, width = img_array.shape[:2]
            
            # Simplified: Detect product-like regions
            # In production: Use trained object detector
            
            # Estimate based on image analysis
            # Look for distinct regions (products separated by gaps)
            gray = np.mean(img_array, axis=2)
            
            # Simple blob detection simulation
            threshold = np.mean(gray)
            binary = gray > threshold
            
            # Count connected regions (simplified product count)
            # In production: Use cv2.findContours or object detection
            estimated_count = int(np.sum(binary) / 5000)  # Rough estimate
            
            return {
                "success": True,
                "product_count": max(1, estimated_count),
                "category": product_category,
                "confidence": 75.0,
                "method": "Computer Vision (Demo)",
                "image_resolution": f"{width}x{height}",
                "counted_at": datetime.now().isoformat(),
                "note": "Production version uses YOLO/Faster R-CNN for accurate counting"
            }
            
        except Exception as e:
            logger.error(f"count_products_on_shelf error: {e}")
            return {"success": False, "error": str(e)}
    
    @staticmethod
    def detect_expiry_date_from_image(image_data: bytes) -> Dict[str, Any]:
        """
        OCR to read expiry dates from product images.
        Automate expiry tracking.
        """
        # This requires Tesseract OCR
        # In production: Use pytesseract or cloud OCR (Google Vision API)
        
        return {
            "success": False,
            "feature": "OCR Expiry Date Detection",
            "status": "requires_tesseract",
            "note": "Install pytesseract and Tesseract OCR for this feature",
            "production_options": [
                "Google Cloud Vision API",
                "AWS Textract",
                "Azure Computer Vision",
                "Tesseract OCR (open source)"
            ],
            "example_result": {
                "detected_text": "EXP: 12/25",
                "expiry_date": "2025-12-12",
                "confidence": 92.5
            }
        }
    
    @staticmethod
    def generate_quality_report(product_id: int, image_data: bytes) -> Dict[str, Any]:
        """
        Comprehensive visual quality inspection report.
        """
        session = get_session()
        try:
            # Get product info using SQLAlchemy ORM
            product = session.query(Product).filter(Product.id == product_id).first()
            
            if not product:
                return {"error": "Product not found"}
            
            product_info = {
                'sku': product.sku,
                'name': product.name,
                'category': product.category
            }
            
            # Run all CV analyses
            freshness = ComputerVisionService.detect_product_freshness(
                image_data, 
                product_info['category']
            )
            
            packaging = ComputerVisionService.detect_damaged_packaging(image_data)
            
            # Overall quality score
            scores = []
            if freshness.get('success'):
                scores.append(freshness['freshness_score'])
            if packaging.get('success'):
                scores.append(100 - packaging['damage_score'])
            
            overall_score = sum(scores) / len(scores) if scores else 0
            
            # Generate recommendation
            if overall_score >= 80:
                action = "SELL_FULL_PRICE"
                recommendation = "Product quality excellent - sell at full price"
            elif overall_score >= 60:
                action = "MINOR_DISCOUNT"
                recommendation = "Good quality - minor discount acceptable"
            elif overall_score >= 40:
                action = "HEAVY_DISCOUNT"
                recommendation = "Quality declining - apply 50%+ discount"
            else:
                action = "REMOVE"
                recommendation = "Poor quality - remove from shelf immediately"
            
            # Store inspection record using SQLAlchemy text query
            result = session.execute(
                text("""
                    INSERT INTO quality_inspections 
                    (product_id, overall_score, freshness_score, packaging_score, 
                     action_required, recommendation, inspected_at)
                    VALUES (:product_id, :overall_score, :freshness_score, :packaging_score, 
                            :action_required, :recommendation, NOW())
                    RETURNING id
                """),
                {
                    'product_id': product_id,
                    'overall_score': overall_score,
                    'freshness_score': freshness.get('freshness_score', 0),
                    'packaging_score': 100 - packaging.get('damage_score', 0) if packaging.get('success') else None,
                    'action_required': action,
                    'recommendation': recommendation
                }
            )
            
            session.commit()
            inspection_id = result.fetchone()[0]
            
            return {
                "success": True,
                "inspection_id": inspection_id,
                "product": product_info,
                "overall_score": round(overall_score, 1),
                "action_required": action,
                "recommendation": recommendation,
                "details": {
                    "freshness_analysis": freshness,
                    "packaging_analysis": packaging
                },
                "inspected_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            session.rollback()
            logger.error(f"generate_quality_report error: {e}")
            return {"success": False, "error": str(e)}
        finally:
            session.close()
    
    @staticmethod
    def monitor_shelf_with_camera(camera_id: str, shop_id: int) -> Dict[str, Any]:
        """
        Continuous shelf monitoring using fixed cameras.
        Real-time alerts for stock issues.
        """
        # In production: Connect to IP camera stream
        # Process frames every N seconds
        # Use object detection to monitor stock levels
        
        return {
            "feature": "Live Camera Monitoring",
            "status": "requires_camera_integration",
            "camera_id": camera_id,
            "shop_id": shop_id,
            "requirements": [
                "IP camera with RTSP stream",
                "OpenCV or similar for frame capture",
                "GPU for real-time inference (optional)",
                "YOLO or similar object detection model"
            ],
            "capabilities": {
                "real_time_stock_monitoring": "Detect when products run low",
                "customer_heatmap": "Track which products get attention",
                "theft_detection": "Alert on suspicious behavior",
                "shelf_compliance": "Ensure proper product placement"
            },
            "example_integration": "cv2.VideoCapture('rtsp://camera-ip:554/stream')"
        }
