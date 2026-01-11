"""
OCR Engine module supporting Tesseract and PaddleOCR.
Provides unified interface for text extraction with bounding boxes.
All operations are CPU-based and offline.
"""

import logging
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import numpy as np
import cv2

logger = logging.getLogger(__name__)


@dataclass
class TextBlock:
    """
    Represents a detected text block with position and confidence.
    """
    text: str
    confidence: float  # 0-1
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    line_index: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class OCRResult:
    """
    Complete OCR result for a document.
    """
    document_id: str
    source_path: str
    page_number: int
    text_blocks: List[TextBlock]
    full_text: str
    avg_confidence: float
    processing_time_seconds: float
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "document_id": self.document_id,
            "source_path": self.source_path,
            "page_number": self.page_number,
            "text_blocks": [block.to_dict() for block in self.text_blocks],
            "full_text": self.full_text,
            "avg_confidence": self.avg_confidence,
            "processing_time_seconds": self.processing_time_seconds
        }


class TesseractOCREngine:
    """
    Tesseract-based OCR engine.
    Requires tesseract-ocr system package installed.
    """
    
    def __init__(self, language: str = "eng", tesseract_path: Optional[str] = None):
        """
        Initialize Tesseract engine.
        
        Args:
            language: Tesseract language code (e.g., 'eng', 'fra')
            tesseract_path: Optional path to tesseract executable
        """
        try:
            import pytesseract
            self.pytesseract = pytesseract
            
            if tesseract_path:
                self.pytesseract.pytesseract.pytesseract_cmd = tesseract_path
            
            self.language = language
            logger.info(f"Initialized Tesseract OCR engine with language: {language}")
        except ImportError:
            raise ImportError("pytesseract not installed. Install with: pip install pytesseract")
    
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image using Tesseract.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult with text blocks and confidence scores
        """
        import time
        start_time = time.time()
        
        try:
            # Extract text with detailed output
            data = self.pytesseract.image_to_data(
                image,
                output_type=self.pytesseract.Output.DICT,
                lang=self.language,
                config='--psm 6'  # Assume uniform block of text
            )
            
            text_blocks = []
            confidences = []
            full_text_parts = []
            line_index = 0
            
            # Process each detected text element
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                
                # Skip empty detections
                if not text:
                    continue
                
                # Get confidence (Tesseract returns -1 for low confidence)
                conf = int(data['conf'][i])
                if conf < 0:
                    conf = 0
                confidence = min(conf / 100.0, 1.0)
                
                # Get bounding box
                x = int(data['left'][i])
                y = int(data['top'][i])
                w = int(data['width'][i])
                h = int(data['height'][i])
                
                block = TextBlock(
                    text=text,
                    confidence=confidence,
                    bbox=(x, y, w, h),
                    x_min=x,
                    y_min=y,
                    x_max=x + w,
                    y_max=y + h,
                    line_index=int(data['line_num'][i]) - 1
                )
                
                text_blocks.append(block)
                confidences.append(confidence)
                full_text_parts.append(text)
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Combine text
            full_text = " ".join(full_text_parts)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"Tesseract extracted {len(text_blocks)} text blocks "
                f"with avg confidence {avg_confidence:.2f} in {processing_time:.2f}s"
            )
            
            return OCRResult(
                document_id="",  # Set by caller
                source_path="",
                page_number=1,
                text_blocks=text_blocks,
                full_text=full_text,
                avg_confidence=avg_confidence,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            logger.error(f"Tesseract extraction failed: {e}")
            raise


class PaddleOCREngine:
    """
    PaddleOCR-based OCR engine.
    Better for Asian languages and various image qualities.
    """
    
    def __init__(self, language: str = "en"):
        """
        Initialize PaddleOCR engine.
        Downloads model on first run (cache for offline use).
        
        Args:
            language: Language code ('en', 'ch', 'fr', etc.)
        """
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=language,
                use_gpu=False  # CPU only
            )
            self.language = language
            logger.info(f"Initialized PaddleOCR engine with language: {language}")
        except ImportError:
            raise ImportError("paddleocr not installed. Install with: pip install paddleocr")
    
    def extract_text(self, image: np.ndarray) -> OCRResult:
        """
        Extract text from image using PaddleOCR.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            OCRResult with text blocks and confidence scores
        """
        import time
        start_time = time.time()
        
        try:
            # Run OCR
            results = self.ocr.ocr(image, cls=True)
            
            text_blocks = []
            confidences = []
            full_text_parts = []
            line_index = 0
            
            # PaddleOCR returns list of (bounding_box, text, confidence)
            if results:
                for line in results:
                    for detection in line:
                        if len(detection) >= 2:
                            bbox_points = detection[0]  # List of 4 points
                            text = detection[1]
                            confidence = float(detection[2]) if len(detection) > 2 else 0.0
                            
                            # Validate text
                            if not text or not isinstance(text, str):
                                continue
                            
                            # Convert bbox format from points to (x, y, w, h)
                            bbox_array = np.array(bbox_points)
                            x_coords = bbox_array[:, 0]
                            y_coords = bbox_array[:, 1]
                            
                            x_min = int(np.min(x_coords))
                            y_min = int(np.min(y_coords))
                            x_max = int(np.max(x_coords))
                            y_max = int(np.max(y_coords))
                            
                            w = x_max - x_min
                            h = y_max - y_min
                            
                            block = TextBlock(
                                text=text.strip(),
                                confidence=confidence,
                                bbox=(x_min, y_min, w, h),
                                x_min=x_min,
                                y_min=y_min,
                                x_max=x_max,
                                y_max=y_max,
                                line_index=line_index
                            )
                            
                            text_blocks.append(block)
                            confidences.append(confidence)
                            full_text_parts.append(text)
                    
                    line_index += 1
            
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # Combine text
            full_text = " ".join(full_text_parts)
            
            processing_time = time.time() - start_time
            
            logger.info(
                f"PaddleOCR extracted {len(text_blocks)} text blocks "
                f"with avg confidence {avg_confidence:.2f} in {processing_time:.2f}s"
            )
            
            return OCRResult(
                document_id="",  # Set by caller
                source_path="",
                page_number=1,
                text_blocks=text_blocks,
                full_text=full_text,
                avg_confidence=avg_confidence,
                processing_time_seconds=processing_time
            )
            
        except Exception as e:
            logger.error(f"PaddleOCR extraction failed: {e}")
            raise


def create_ocr_engine(engine_type: str = "tesseract", **kwargs) -> TesseractOCREngine | PaddleOCREngine:
    """
    Factory function to create OCR engine.
    
    Args:
        engine_type: "tesseract" or "paddleocr"
        **kwargs: Additional arguments for engine initialization
        
    Returns:
        Initialized OCR engine
    """
    if engine_type.lower() == "tesseract":
        return TesseractOCREngine(**kwargs)
    elif engine_type.lower() == "paddleocr":
        return PaddleOCREngine(**kwargs)
    else:
        raise ValueError(f"Unknown OCR engine: {engine_type}")
