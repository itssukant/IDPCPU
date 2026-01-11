"""
Pydantic models for backend API.
Defines request/response schemas for all endpoints.
"""

from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from datetime import datetime
import uuid


class DocumentTypeEnum(str, Enum):
    """Supported document types."""
    INVOICE = "invoice"
    RECEIPT = "receipt"
    FORM = "form"
    CONTRACT = "contract"
    GENERAL = "general"


class ProcessingStatusEnum(str, Enum):
    """Document processing status."""
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DocumentUploadRequest(BaseModel):
    """Request model for document upload."""
    document_type: DocumentTypeEnum = Field(default=DocumentTypeEnum.GENERAL)
    metadata: Optional[Dict[str, Any]] = Field(default={})
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_type": "invoice",
                "metadata": {"source": "vendor_123", "date_received": "2024-01-11"}
            }
        }


class DocumentUploadResponse(BaseModel):
    """Response after document upload."""
    document_id: str
    filename: str
    document_type: str
    size_bytes: int
    upload_timestamp: datetime
    status: ProcessingStatusEnum
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_id": "doc_xyz123",
                "filename": "invoice_001.pdf",
                "document_type": "invoice",
                "size_bytes": 245600,
                "upload_timestamp": "2024-01-11T10:30:00",
                "status": "pending"
            }
        }


class TextBlockModel(BaseModel):
    """Single text block from OCR."""
    text: str
    confidence: float = Field(ge=0, le=1)
    bbox: tuple  # (x, y, w, h)
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    line_index: int = 0


class OCRResultModel(BaseModel):
    """OCR processing result."""
    document_id: str
    full_text: str
    text_blocks: List[TextBlockModel]
    avg_confidence: float = Field(ge=0, le=1)
    page_number: int = 1
    processing_time_seconds: float


class TableCellModel(BaseModel):
    """Single cell in extracted table."""
    row_index: int
    col_index: int
    text: str
    confidence: float


class TableModel(BaseModel):
    """Detected table structure."""
    table_id: str
    rows: int
    columns: int
    cells: List[TableCellModel]
    bounding_box: tuple  # (x_min, y_min, x_max, y_max)


class TextRegionModel(BaseModel):
    """Logical region of text."""
    region_id: str
    text_blocks_indices: List[int]
    region_type: str
    bounding_box: tuple


class LayoutAnalysisModel(BaseModel):
    """Layout analysis result."""
    document_id: str
    regions: List[TextRegionModel]
    tables: List[TableModel]
    key_value_pairs: Dict[str, str]


class ExtractionResultModel(BaseModel):
    """LLM extraction result."""
    document_id: str
    extracted_data: Dict[str, Any]
    confidence: float = Field(ge=0, le=1)
    processing_time_seconds: float
    validation_status: Optional[str] = None


class ProcessingResultModel(BaseModel):
    """Complete processing result for a document."""
    document_id: str
    status: ProcessingStatusEnum
    filename: str
    document_type: str
    created_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results from each pipeline stage
    ocr_result: Optional[OCRResultModel] = None
    layout_result: Optional[LayoutAnalysisModel] = None
    extraction_result: Optional[ExtractionResultModel] = None
    
    # Validation
    validation_passed: Optional[bool] = None
    validation_errors: List[str] = []
    
    # Metadata
    error_message: Optional[str] = None
    processing_time_seconds: float = 0.0


class ProcessingStatusRequest(BaseModel):
    """Request to check processing status."""
    document_id: str


class ExtractedFieldModel(BaseModel):
    """Single extracted field for editing."""
    field_name: str
    original_value: Any
    corrected_value: Optional[Any] = None
    confidence: float = Field(ge=0, le=1)
    source_text: Optional[str] = None


class ManualCorrectionRequest(BaseModel):
    """Request to manually correct extracted fields."""
    document_id: str
    corrections: Dict[str, Any] = Field(description="Field name to corrected value")
    notes: Optional[str] = None


class ValidateExtractionRequest(BaseModel):
    """Request to validate extraction against custom rules."""
    document_id: str
    extracted_data: Dict[str, Any]
    schema_id: Optional[str] = None


class ValidationResultModel(BaseModel):
    """Result of validation."""
    document_id: str
    is_valid: bool
    errors: List[Dict[str, str]] = []  # [{field, error_message}]
    warnings: List[Dict[str, str]] = []
    confidence_score: float = Field(ge=0, le=1)


class ExportRequest(BaseModel):
    """Request to export results."""
    document_id: str
    format: str = Field(regex="^(json|csv|xml)$")
    include_ocr: bool = False
    include_layout: bool = False


class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    components: Dict[str, str]  # Component name to status


class ErrorResponse(BaseModel):
    """Standard error response."""
    error_code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "error_code": "INVALID_FILE_TYPE",
                "message": "File type not supported",
                "details": {"supported_types": ["pdf", "jpg", "png"]},
                "timestamp": "2024-01-11T10:30:00"
            }
        }
