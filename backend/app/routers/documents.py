"""
Main API routes for document processing.
"""

import logging
import uuid
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, Query, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
import aiofiles

from config import settings
from backend.app.models import (
    DocumentUploadRequest,
    DocumentUploadResponse,
    ProcessingStatusRequest,
    ProcessingResultModel,
    ProcessingStatusEnum,
    ManualCorrectionRequest,
    ValidateExtractionRequest,
    ValidationResultModel,
    ExportRequest,
    HealthCheckResponse,
    ErrorResponse
)
from backend.app.services import ProcessingService

router = APIRouter(prefix="/documents", tags=["documents"])
logger = logging.getLogger(__name__)

# Global service instance
_service: Optional[ProcessingService] = None
_processing_jobs = {}  # document_id -> processing_result


def get_service() -> ProcessingService:
    """Get or initialize the processing service."""
    global _service
    if _service is None:
        _service = ProcessingService()
    return _service


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = Query("general"),
    background_tasks: BackgroundTasks = None
) -> DocumentUploadResponse:
    """
    Upload a document for processing.
    
    Supported formats: PDF, JPG, PNG
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type .{file_ext} not supported. "
            f"Supported: {', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # Generate document ID
    document_id = f"doc_{uuid.uuid4().hex[:12]}"
    
    # Create upload directory
    settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save file
    file_path = settings.UPLOAD_DIR / f"{document_id}_{file.filename}"
    
    try:
        # Validate file size
        content = await file.read()
        if len(content) > settings.MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed: "
                f"{settings.MAX_UPLOAD_SIZE_MB}MB"
            )
        
        # Save file
        async with aiofiles.open(str(file_path), "wb") as f:
            await f.write(content)
        
        logger.info(f"Document uploaded: {document_id}, size: {len(content)} bytes")
        
        # Schedule background processing if needed
        if background_tasks:
            background_tasks.add_task(
                process_document_background,
                document_id,
                str(file_path),
                document_type
            )
        
        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            document_type=document_type,
            size_bytes=len(content),
            upload_timestamp=datetime.utcnow(),
            status=ProcessingStatusEnum.PENDING
        )
    
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.post("/process/{document_id}")
async def process_document(
    document_id: str,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Start processing for a previously uploaded document.
    Processing runs in background.
    """
    # Find uploaded file
    uploaded_files = list(settings.UPLOAD_DIR.glob(f"{document_id}_*"))
    
    if not uploaded_files:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    
    file_path = str(uploaded_files[0])
    
    # Schedule processing
    background_tasks.add_task(
        process_document_background,
        document_id,
        file_path,
        "general"
    )
    
    logger.info(f"Processing started for document: {document_id}")
    
    return {
        "document_id": document_id,
        "status": "processing",
        "message": "Document processing started. Check status endpoint for updates."
    }


async def process_document_background(
    document_id: str,
    file_path: str,
    document_type: str
):
    """Background task to process document."""
    try:
        _processing_jobs[document_id] = {
            "status": ProcessingStatusEnum.PROCESSING,
            "started_at": datetime.utcnow()
        }
        
        service = get_service()
        result = await service.process_document(
            file_path,
            document_id,
            document_type
        )
        
        _processing_jobs[document_id] = {
            "status": ProcessingStatusEnum.COMPLETED,
            "result": result,
            "completed_at": datetime.utcnow()
        }
        
        logger.info(f"Document processing completed: {document_id}")
    
    except Exception as e:
        logger.error(f"Background processing failed for {document_id}: {e}")
        _processing_jobs[document_id] = {
            "status": ProcessingStatusEnum.FAILED,
            "error": str(e),
            "completed_at": datetime.utcnow()
        }


@router.get("/status/{document_id}")
async def get_status(document_id: str) -> dict:
    """Get processing status and results for a document."""
    if document_id not in _processing_jobs:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    
    job = _processing_jobs[document_id]
    
    response = {
        "document_id": document_id,
        "status": job["status"],
        "started_at": job.get("started_at"),
        "completed_at": job.get("completed_at")
    }
    
    if job["status"] == ProcessingStatusEnum.COMPLETED:
        response["result"] = job.get("result")
    elif job["status"] == ProcessingStatusEnum.FAILED:
        response["error"] = job.get("error")
    
    return response


@router.post("/correct/{document_id}")
async def correct_extraction(
    document_id: str,
    request: ManualCorrectionRequest
) -> dict:
    """
    Manually correct extracted fields.
    """
    if document_id not in _processing_jobs:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    
    job = _processing_jobs[document_id]
    if job["status"] != ProcessingStatusEnum.COMPLETED:
        raise HTTPException(status_code=400, detail="Document not yet processed")
    
    # Update extraction result with corrections
    if "result" in job and "extraction" in job["result"]:
        for field, value in request.corrections.items():
            job["result"]["extraction"]["data"][field] = value
        
        logger.info(
            f"Applied {len(request.corrections)} corrections to document: {document_id}"
        )
        
        return {
            "document_id": document_id,
            "message": "Corrections applied successfully",
            "corrected_fields": list(request.corrections.keys())
        }
    
    raise HTTPException(status_code=400, detail="No extraction data to correct")


@router.post("/validate/{document_id}")
async def validate_extraction(
    document_id: str,
    request: ValidateExtractionRequest
) -> ValidationResultModel:
    """
    Validate extraction against rules.
    """
    service = get_service()
    validation_result = await service._validate_extraction(
        request.extracted_data,
        document_id
    )
    
    return ValidationResultModel(
        document_id=document_id,
        is_valid=validation_result.get("is_valid", False),
        errors=validation_result.get("errors", []),
        warnings=validation_result.get("warnings", []),
        confidence_score=0.95 if validation_result.get("is_valid") else 0.5
    )


@router.post("/export/{document_id}")
async def export_results(
    document_id: str,
    request: ExportRequest
) -> FileResponse:
    """
    Export processing results in requested format.
    """
    if document_id not in _processing_jobs:
        raise HTTPException(status_code=404, detail=f"Document not found: {document_id}")
    
    job = _processing_jobs[document_id]
    if job["status"] != ProcessingStatusEnum.COMPLETED:
        raise HTTPException(status_code=400, detail="Document not yet processed")
    
    result = job.get("result", {})
    
    # Prepare export data
    export_data = {"document_id": document_id}
    
    if request.include_ocr and "ocr" in result:
        export_data["ocr"] = result["ocr"]
    
    if request.include_layout and "layout" in result:
        export_data["layout"] = result["layout"]
    
    if "extraction" in result:
        export_data["extraction"] = result["extraction"]
    
    # Generate export file
    export_dir = settings.UPLOAD_DIR / "exports"
    export_dir.mkdir(exist_ok=True)
    
    if request.format == "json":
        import json
        export_file = export_dir / f"{document_id}_export.json"
        with open(export_file, "w") as f:
            json.dump(export_data, f, indent=2, default=str)
        return FileResponse(export_file, filename=f"{document_id}_export.json")
    
    elif request.format == "csv":
        import csv
        export_file = export_dir / f"{document_id}_export.csv"
        
        extraction_data = export_data.get("extraction", {}).get("data", {})
        
        with open(export_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Field", "Value"])
            for key, value in extraction_data.items():
                writer.writerow([key, value])
        
        return FileResponse(export_file, filename=f"{document_id}_export.csv")
    
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {request.format}")


@router.get("/health", response_model=HealthCheckResponse)
async def health_check() -> HealthCheckResponse:
    """Health check endpoint."""
    service = get_service()
    
    components = {
        "ocr": "healthy" if service.ocr_engine else "disabled",
        "layout": "healthy" if service.layout_analyzer else "disabled",
        "llm": "healthy" if service.llm_engine else "disabled"
    }
    
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        components=components
    )
