"""
OCR module initialization.
"""

from .engine import (
    OCRResult,
    TextBlock,
    TesseractOCREngine,
    PaddleOCREngine,
    create_ocr_engine
)
from .preprocessor import ImagePreprocessor

__all__ = [
    "OCRResult",
    "TextBlock",
    "TesseractOCREngine",
    "PaddleOCREngine",
    "create_ocr_engine",
    "ImagePreprocessor"
]
