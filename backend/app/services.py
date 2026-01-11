"""
Document processing service.
Core business logic for the pipeline.
"""

import logging
import asyncio
import json
import os
from typing import Optional, Dict, Any
from pathlib import Path
import uuid
from datetime import datetime
import time

from inference import (
    create_ocr_engine,
    ImagePreprocessor,
    LayoutAnalyzer,
    LlamaInferenceEngine,
    PromptBuilder
)
from config import settings
from pdf2image import convert_from_path

logger = logging.getLogger(__name__)


class ProcessingService:
    """
    Orchestrates the complete document processing pipeline.
    Manages OCR, layout analysis, and LLM extraction.
    """
    
    def __init__(self):
        """Initialize the service with all required engines."""
        self.preprocessor = ImagePreprocessor(
            deskew=settings.DESKEW_ENABLED,
            denoise=settings.DENOISE_ENABLED,
            binarization=settings.BINARIZATION_ENABLED
        )
        
        self.ocr_engine = None
        self.layout_analyzer = LayoutAnalyzer(
            proximity_threshold=settings.PROXIMITY_THRESHOLD,
            min_block_height=settings.MIN_TEXT_BLOCK_HEIGHT,
            min_block_width=settings.MIN_TEXT_BLOCK_WIDTH,
            table_row_threshold=settings.TABLE_ROW_THRESHOLD
        )
        
        self.llm_engine = None
        self.prompt_builder = PromptBuilder()
        
        # Initialize OCR engine
        if settings.ENABLE_OCR:
            try:
                self.ocr_engine = create_ocr_engine(
                    engine_type=settings.OCR_ENGINE,
                    language=settings.OCR_LANGUAGE,
                    tesseract_path=settings.TESSERACT_PATH
                )
                logger.info(f"OCR engine initialized: {settings.OCR_ENGINE}")
            except Exception as e:
                logger.error(f"Failed to initialize OCR engine: {e}")
                logger.warning("OCR will be disabled")
        
        # Initialize LLM engine
        if settings.ENABLE_LLM_EXTRACTION:
            try:
                # Check if model file exists
                if Path(settings.LLM_MODEL_PATH).exists():
                    self.llm_engine = LlamaInferenceEngine(
                        model_path=settings.LLM_MODEL_PATH,
                        context_tokens=settings.LLM_CONTEXT_TOKENS,
                        max_tokens=settings.LLM_MAX_TOKENS,
                        temperature=settings.LLM_TEMPERATURE,
                        top_p=settings.LLM_TOP_P,
                        n_threads=settings.LLM_N_THREADS,
                        verbose=settings.DEBUG
                    )
                    logger.info("LLM engine initialized successfully")
                else:
                    logger.warning(
                        f"LLM model not found at {settings.LLM_MODEL_PATH}. "
                        f"LLM extraction will be disabled. "
                        f"Download a GGUF model to enable this feature."
                    )
            except Exception as e:
                logger.error(f"Failed to initialize LLM engine: {e}")
                logger.warning("LLM extraction will be disabled")
    
    async def process_document(
        self,
        image_path: str,
        document_id: str,
        document_type: str = "general",
        json_schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a document through the complete pipeline.
        
        Args:
            image_path: Path to preprocessed image
            document_id: Unique document identifier
            document_type: Type of document (invoice, form, etc.)
            json_schema: Optional JSON schema for extraction validation
            
        Returns:
            Dictionary with complete processing results
        """
        start_time = time.time()
        results = {
            "document_id": document_id,
            "document_type": document_type,
            "timestamp": datetime.utcnow().isoformat(),
            "pipeline": {}
        }
        
        try:
            # Stage 0: If PDF, convert first page to image
            suffix = Path(image_path).suffix.lower()
            if suffix == ".pdf":
                logger.info(f"Converting PDF to image for {document_id}")
                poppler_path = os.getenv("POPPLER_PATH")  # optional for macOS/Homebrew
                images = convert_from_path(
                    image_path,
                    dpi=300,
                    poppler_path=poppler_path
                )
                if not images:
                    raise ValueError("PDF to image conversion produced no pages")
                temp_image_path = settings.UPLOAD_DIR / f"{document_id}_page1.png"
                images[0].save(temp_image_path, format="PNG")
                image_path = str(temp_image_path)
                logger.info(f"PDF converted to image: {image_path}")
            
            # Stage 1: Preprocessing
            logger.info(f"Starting preprocessing for {document_id}")
            preprocessed_image = self.preprocessor.process(image_path)
            results["pipeline"]["preprocessing"] = {"status": "success"}
            
            # Stage 2: OCR
            if settings.ENABLE_OCR and self.ocr_engine:
                logger.info(f"Starting OCR for {document_id}")
                try:
                    ocr_result = self.ocr_engine.extract_text(preprocessed_image)
                    ocr_result.document_id = document_id
                    ocr_result.source_path = image_path
                    
                    # Filter by confidence threshold
                    filtered_blocks = [
                        block for block in ocr_result.text_blocks
                        if block.confidence >= settings.MIN_OCR_CONFIDENCE
                    ]
                    
                    results["ocr"] = {
                        "full_text": ocr_result.full_text,
                        "confidence": ocr_result.avg_confidence,
                        "text_blocks": [b.to_dict() for b in filtered_blocks],
                        "processing_time": ocr_result.processing_time_seconds,
                        "engine": settings.OCR_ENGINE
                    }
                    results["pipeline"]["ocr"] = {"status": "success"}
                    
                    logger.info(
                        f"OCR completed: {len(filtered_blocks)} blocks, "
                        f"confidence: {ocr_result.avg_confidence:.2f}"
                    )
                    
                except Exception as e:
                    logger.error(f"OCR failed: {e}")
                    results["pipeline"]["ocr"] = {"status": "failed", "error": str(e)}
                    results["ocr"] = None
            
            # Stage 3: Layout Analysis
            if settings.ENABLE_LAYOUT_ANALYSIS and results.get("ocr"):
                logger.info(f"Starting layout analysis for {document_id}")
                try:
                    # Reconstruct text blocks for layout analyzer
                    text_blocks = []
                    for block_dict in results["ocr"]["text_blocks"]:
                        # Create simple object with required attributes
                        class SimpleBlock:
                            def __init__(self, data):
                                self.text = data["text"]
                                self.confidence = data["confidence"]
                                self.bbox = data["bbox"]
                                self.x_min = data["x_min"]
                                self.y_min = data["y_min"]
                                self.x_max = data["x_max"]
                                self.y_max = data["y_max"]
                        
                        text_blocks.append(SimpleBlock(block_dict))
                    
                    layout_result = self.layout_analyzer.analyze(text_blocks)
                    layout_result.document_id = document_id
                    
                    results["layout"] = layout_result.to_dict()
                    results["pipeline"]["layout"] = {"status": "success"}
                    
                    logger.info(
                        f"Layout analysis completed: {len(layout_result.regions)} regions, "
                        f"{len(layout_result.tables)} tables"
                    )
                    
                except Exception as e:
                    logger.error(f"Layout analysis failed: {e}")
                    results["pipeline"]["layout"] = {"status": "failed", "error": str(e)}
                    results["layout"] = None
            
            # Stage 4: LLM Extraction
            if settings.ENABLE_LLM_EXTRACTION and self.llm_engine and results.get("ocr"):
                logger.info(f"Starting LLM extraction for {document_id}")
                try:
                    # Sanitize OCR text (remove sensitive patterns if needed)
                    sanitized_text = self._sanitize_text(results["ocr"]["full_text"])
                    
                    # Build extraction prompt
                    extraction_schema = json_schema or self._get_default_schema(document_type)
                    prompt = self.prompt_builder.build_extraction_prompt(
                        schema=extraction_schema,
                        system_instructions=f"Document type: {document_type}"
                    )
                    
                    # Run extraction
                    llm_result = self.llm_engine.extract(
                        prompt=prompt,
                        json_schema=extraction_schema,
                        sanitized_text=sanitized_text
                    )
                    
                    if llm_result.error:
                        logger.error(f"LLM extraction error: {llm_result.error}")
                        results["pipeline"]["extraction"] = {
                            "status": "failed",
                            "error": llm_result.error
                        }
                        results["extraction"] = None
                    else:
                        results["extraction"] = {
                            "data": llm_result.extracted_data,
                            "confidence": llm_result.confidence,
                            "raw_response": llm_result.raw_response if settings.DEBUG else None,
                            "processing_time": llm_result.processing_time_seconds,
                            "tokens_used": llm_result.tokens_used,
                            "model": llm_result.model_name
                        }
                        results["pipeline"]["extraction"] = {"status": "success"}
                        
                        logger.info(
                            f"LLM extraction completed: confidence {llm_result.confidence:.2f}, "
                            f"{len(llm_result.extracted_data)} fields"
                        )
                
                except Exception as e:
                    logger.error(f"LLM extraction failed: {e}")
                    results["pipeline"]["extraction"] = {"status": "failed", "error": str(e)}
                    results["extraction"] = None
            
            # Stage 5: Validation (if enabled)
            if settings.ENABLE_VALIDATION and results.get("extraction"):
                logger.info(f"Starting validation for {document_id}")
                try:
                    validation_result = await self._validate_extraction(
                        results["extraction"]["data"],
                        document_type
                    )
                    results["validation"] = validation_result
                    results["pipeline"]["validation"] = {"status": "success"}
                except Exception as e:
                    logger.error(f"Validation failed: {e}")
                    results["validation"] = {"status": "failed", "error": str(e)}
            
            # Final timing
            total_time = time.time() - start_time
            results["total_processing_time"] = total_time
            results["status"] = "completed"
            
            logger.info(f"Document {document_id} processing completed in {total_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Unexpected error processing document: {e}")
            results["status"] = "failed"
            results["error"] = str(e)
        
        return results
    
    def _sanitize_text(self, text: str) -> str:
        """
        Sanitize OCR text before sending to LLM.
        Removes or masks sensitive patterns (SSN, credit cards, etc.)
        """
        # This is a basic implementation
        # In production, implement more comprehensive sanitization
        if settings.LOG_SUPPRESS_SENSITIVE_DATA:
            # Mask common sensitive patterns
            import re
            
            # Mask SSN
            text = re.sub(r'\d{3}-\d{2}-\d{4}', '[SSN]', text)
            
            # Mask credit card
            text = re.sub(r'\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}', '[CARD]', text)
            
            logger.debug("Applied text sanitization")
        
        return text
    
    def _get_default_schema(self, document_type: str) -> Dict[str, Any]:
        """Get default schema for document type."""
        schemas = {
            "invoice": {
                "type": "object",
                "properties": {
                    "invoice_number": {"type": ["string", "null"]},
                    "date": {"type": ["string", "null"]},
                    "vendor": {"type": ["string", "null"]},
                    "total_amount": {"type": ["number", "null"]},
                    "items": {"type": ["array", "null"]},
                    "due_date": {"type": ["string", "null"]}
                }
            },
            "form": {
                "type": "object",
                "properties": {
                    "form_id": {"type": ["string", "null"]},
                    "fields": {"type": ["object", "null"]}
                }
            },
            "general": {
                "type": "object",
                "properties": {
                    "content": {"type": ["string", "null"]},
                    "key_fields": {"type": ["object", "null"]}
                }
            }
        }
        
        return schemas.get(document_type, schemas["general"])
    
    async def _validate_extraction(
        self,
        extracted_data: Dict[str, Any],
        document_type: str
    ) -> Dict[str, Any]:
        """
        Validate extracted data against business rules.
        """
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        # Add document-type-specific validation logic here
        if document_type == "invoice":
            # Validate invoice-specific fields
            if not extracted_data.get("invoice_number"):
                validation_result["errors"].append("Missing invoice number")
                validation_result["is_valid"] = False
            
            if not extracted_data.get("total_amount"):
                validation_result["warnings"].append("Missing total amount")
        
        return validation_result
