"""
Example usage of the IDP system.
Demonstrates API calls and integration patterns.
"""

import json
import requests
from pathlib import Path

# API Configuration
API_BASE = "http://localhost:8000/api/v1"
UPLOAD_TIMEOUT = 30
PROCESSING_TIMEOUT = 300


class IDPClient:
    """Client for interacting with IDP API."""
    
    def __init__(self, base_url: str = API_BASE):
        self.base_url = base_url
        self.session = requests.Session()
    
    def upload_document(
        self,
        file_path: str,
        document_type: str = "general"
    ) -> dict:
        """
        Upload a document for processing.
        
        Args:
            file_path: Path to document file
            document_type: Type of document (general, invoice, receipt, form)
            
        Returns:
            Upload response with document_id
        """
        with open(file_path, "rb") as f:
            files = {"file": f}
            params = {"document_type": document_type}
            
            response = self.session.post(
                f"{self.base_url}/documents/upload",
                files=files,
                params=params,
                timeout=UPLOAD_TIMEOUT
            )
            response.raise_for_status()
            
            return response.json()
    
    def get_status(self, document_id: str) -> dict:
        """Get processing status and results."""
        response = self.session.get(
            f"{self.base_url}/documents/status/{document_id}",
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def correct_extraction(
        self,
        document_id: str,
        corrections: dict,
        notes: str = ""
    ) -> dict:
        """Apply manual corrections to extracted data."""
        payload = {
            "document_id": document_id,
            "corrections": corrections,
            "notes": notes
        }
        
        response = self.session.post(
            f"{self.base_url}/documents/correct/{document_id}",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def validate_extraction(
        self,
        document_id: str,
        extracted_data: dict
    ) -> dict:
        """Validate extracted data against rules."""
        payload = {
            "document_id": document_id,
            "extracted_data": extracted_data
        }
        
        response = self.session.post(
            f"{self.base_url}/documents/validate/{document_id}",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.json()
    
    def export_results(
        self,
        document_id: str,
        format: str = "json",
        include_ocr: bool = False,
        include_layout: bool = False
    ) -> bytes:
        """Export results in requested format."""
        payload = {
            "document_id": document_id,
            "format": format,
            "include_ocr": include_ocr,
            "include_layout": include_layout
        }
        
        response = self.session.post(
            f"{self.base_url}/documents/export/{document_id}",
            json=payload,
            timeout=30
        )
        response.raise_for_status()
        return response.content
    
    def health_check(self) -> dict:
        """Check system health."""
        response = self.session.get(
            f"{self.base_url}/documents/health",
            timeout=10
        )
        response.raise_for_status()
        return response.json()


def example_invoice_processing():
    """Example: Process an invoice."""
    client = IDPClient()
    
    # 1. Check system health
    print("Checking system health...")
    health = client.health_check()
    print(f"System Status: {health['status']}")
    print(f"Components: {health['components']}")
    
    # 2. Upload invoice
    print("\nUploading invoice...")
    upload_response = client.upload_document(
        file_path="examples/sample_invoice.pdf",
        document_type="invoice"
    )
    document_id = upload_response["document_id"]
    print(f"Document uploaded: {document_id}")
    print(f"File: {upload_response['filename']}")
    print(f"Size: {upload_response['size_bytes']} bytes")
    
    # 3. Wait for processing
    import time
    print("\nWaiting for processing...")
    max_wait = 300  # 5 minutes
    elapsed = 0
    
    while elapsed < max_wait:
        status = client.get_status(document_id)
        
        if status["status"] == "completed":
            print("Processing complete!")
            break
        elif status["status"] == "failed":
            print(f"Processing failed: {status.get('error')}")
            return
        
        print(f"Status: {status['status']}")
        time.sleep(5)
        elapsed += 5
    
    # 4. Review extraction results
    print("\nExtracted Data:")
    result = status.get("result", {})
    if "extraction" in result:
        extraction = result["extraction"]
        print(json.dumps(extraction["data"], indent=2))
        print(f"Confidence: {extraction['confidence']:.2%}")
        print(f"Processing time: {extraction['processing_time']:.2f}s")
    
    # 5. Apply corrections if needed
    if "extraction" in result:
        print("\nApplying manual corrections...")
        corrections = {
            "invoice_number": "INV-2024-001",  # Corrected value
        }
        
        correct_response = client.correct_extraction(
            document_id,
            corrections,
            notes="Corrected invoice number from OCR error"
        )
        print(f"Corrections applied: {correct_response['corrected_fields']}")
    
    # 6. Validate
    print("\nValidating extraction...")
    if "extraction" in result:
        validation = client.validate_extraction(
            document_id,
            result["extraction"]["data"]
        )
        print(f"Validation passed: {validation['is_valid']}")
        if validation['errors']:
            print(f"Errors: {validation['errors']}")
    
    # 7. Export results
    print("\nExporting results...")
    json_export = client.export_results(
        document_id,
        format="json",
        include_ocr=True
    )
    with open(f"results_{document_id}.json", "wb") as f:
        f.write(json_export)
    print(f"Results exported to: results_{document_id}.json")


def example_batch_processing():
    """Example: Process multiple documents."""
    client = IDPClient()
    documents_dir = Path("examples/documents")
    
    if not documents_dir.exists():
        print("No documents directory found")
        return
    
    results = {}
    
    # Upload all documents
    for file_path in documents_dir.glob("*.pdf"):
        print(f"Uploading {file_path.name}...")
        response = client.upload_document(
            str(file_path),
            document_type="invoice"
        )
        doc_id = response["document_id"]
        results[doc_id] = {
            "file": file_path.name,
            "status": "pending"
        }
    
    # Wait for all to complete
    import time
    completed = 0
    max_attempts = 120
    attempts = 0
    
    while completed < len(results) and attempts < max_attempts:
        for doc_id in results:
            if results[doc_id]["status"] == "pending":
                status = client.get_status(doc_id)
                
                if status["status"] == "completed":
                    results[doc_id]["status"] = "completed"
                    results[doc_id]["result"] = status.get("result")
                    completed += 1
                    print(f"✓ {results[doc_id]['file']} processed")
                elif status["status"] == "failed":
                    results[doc_id]["status"] = "failed"
                    results[doc_id]["error"] = status.get("error")
                    completed += 1
                    print(f"✗ {results[doc_id]['file']} failed")
        
        time.sleep(5)
        attempts += 1
    
    # Summary
    print("\n=== Batch Processing Summary ===")
    successful = sum(1 for r in results.values() if r["status"] == "completed")
    print(f"Processed: {successful}/{len(results)} documents")
    
    # Export all results
    all_results = {}
    for doc_id, info in results.items():
        if info["status"] == "completed":
            all_results[doc_id] = info["result"]
    
    with open("batch_results.json", "w") as f:
        json.dump(all_results, f, indent=2, default=str)
    print("Results saved to: batch_results.json")


def example_api_request_response():
    """Example: Raw API request and response."""
    
    # Example: Upload request
    print("=== Upload Request ===")
    print("POST /api/v1/documents/upload")
    print("Content-Type: multipart/form-data")
    print("file: (binary)")
    print("document_type: invoice")
    
    print("\n=== Upload Response ===")
    example_upload_response = {
        "document_id": "doc_abc123xyz456",
        "filename": "invoice_2024_01.pdf",
        "document_type": "invoice",
        "size_bytes": 245600,
        "upload_timestamp": "2024-01-11T10:30:00",
        "status": "pending"
    }
    print(json.dumps(example_upload_response, indent=2))
    
    # Example: Status request
    print("\n\n=== Status Request ===")
    print("GET /api/v1/documents/status/doc_abc123xyz456")
    
    print("\n=== Status Response (Completed) ===")
    example_status_response = {
        "document_id": "doc_abc123xyz456",
        "status": "completed",
        "started_at": "2024-01-11T10:30:05",
        "completed_at": "2024-01-11T10:35:12",
        "result": {
            "extraction": {
                "data": {
                    "invoice_number": "INV-2024-001",
                    "invoice_date": "2024-01-08",
                    "due_date": "2024-02-08",
                    "vendor_name": "ACME Corporation",
                    "total_amount": 5250.00,
                    "currency": "USD"
                },
                "confidence": 0.92,
                "processing_time": 12.5,
                "tokens_used": 245,
                "model": "llama-7b-quantized"
            },
            "ocr": {
                "full_text": "Invoice INV-2024-001...",
                "confidence": 0.87,
                "text_blocks": 24
            }
        }
    }
    print(json.dumps(example_status_response, indent=2, default=str))


if __name__ == "__main__":
    print("IDP System Examples\n")
    
    try:
        # Uncomment to run examples:
        
        # Single document processing
        # example_invoice_processing()
        
        # Batch processing
        # example_batch_processing()
        
        # API examples
        example_api_request_response()
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
