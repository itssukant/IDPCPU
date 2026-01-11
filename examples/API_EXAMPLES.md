# Example API Requests & Responses

## Authentication & Health Check

### Health Check

**Request:**
```http
GET /api/v1/documents/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "ocr": "healthy",
    "layout": "healthy",
    "llm": "healthy"
  }
}
```

---

## Document Upload

### Upload Invoice PDF

**Request:**
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: (binary PDF data)
document_type: invoice
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "filename": "invoice_2024_01.pdf",
  "document_type": "invoice",
  "size_bytes": 245600,
  "upload_timestamp": "2024-01-11T10:30:00",
  "status": "pending"
}
```

### Upload Receipt Image

**Request:**
```http
POST /api/v1/documents/upload
Content-Type: multipart/form-data

file: (binary PNG/JPG data)
document_type: receipt
```

**Response (200 OK):**
```json
{
  "document_id": "doc_x9y8z7w6v5u4",
  "filename": "receipt_scan.jpg",
  "document_type": "receipt",
  "size_bytes": 1024000,
  "upload_timestamp": "2024-01-11T10:30:30",
  "status": "pending"
}
```

### Error: Invalid File Type

**Response (400 Bad Request):**
```json
{
  "error_code": "INVALID_FILE_TYPE",
  "message": "File type not supported",
  "details": {
    "supported_types": ["pdf", "jpg", "jpeg", "png"]
  },
  "timestamp": "2024-01-11T10:30:45"
}
```

### Error: File Too Large

**Response (413 Request Entity Too Large):**
```json
{
  "error_code": "FILE_TOO_LARGE",
  "message": "File size exceeds maximum allowed: 50MB",
  "timestamp": "2024-01-11T10:31:00"
}
```

---

## Processing & Status

### Start Processing

**Request:**
```http
POST /api/v1/documents/process/doc_a1b2c3d4e5f6
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "status": "processing",
  "message": "Document processing started. Check status endpoint for updates."
}
```

### Check Status (Processing)

**Request:**
```http
GET /api/v1/documents/status/doc_a1b2c3d4e5f6
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "status": "processing",
  "started_at": "2024-01-11T10:30:05",
  "completed_at": null
}
```

### Check Status (Completed)

**Request:**
```http
GET /api/v1/documents/status/doc_a1b2c3d4e5f6
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "status": "completed",
  "started_at": "2024-01-11T10:30:05",
  "completed_at": "2024-01-11T10:35:12",
  "result": {
    "ocr": {
      "full_text": "Invoice INV-2024-001\nDate: January 8, 2024\nVendor: ACME Corporation\n...",
      "confidence": 0.87,
      "text_blocks": 24,
      "processing_time": 8.5,
      "engine": "tesseract"
    },
    "layout": {
      "regions": [
        {
          "region_id": "region_0",
          "text_blocks_indices": [0, 1, 2],
          "region_type": "body",
          "bounding_box": [50, 100, 500, 200]
        }
      ],
      "tables": [
        {
          "table_id": "table_0",
          "rows": 4,
          "columns": 3,
          "cells": [
            {
              "row_index": 0,
              "col_index": 0,
              "text": "Item",
              "confidence": 0.95
            }
          ],
          "bounding_box": [50, 300, 500, 400]
        }
      ],
      "key_value_pairs": {
        "Invoice Number": "INV-2024-001",
        "Date": "January 8, 2024"
      }
    },
    "extraction": {
      "data": {
        "invoice_number": "INV-2024-001",
        "invoice_date": "2024-01-08",
        "due_date": "2024-02-08",
        "vendor_name": "ACME Corporation",
        "vendor_address": "123 Business Ave, Suite 100, New York, NY 10001",
        "vendor_tax_id": "12-3456789",
        "customer_name": "XYZ Company",
        "customer_address": "456 Commerce St, Los Angeles, CA 90001",
        "items": [
          {
            "description": "Professional Services - Consulting",
            "quantity": 1,
            "unit_price": 5000.00,
            "total": 5000.00
          },
          {
            "description": "Maintenance & Support",
            "quantity": 1,
            "unit_price": 250.00,
            "total": 250.00
          }
        ],
        "subtotal": 5250.00,
        "tax_rate": 8.5,
        "tax_amount": 446.25,
        "total_amount": 5696.25,
        "currency": "USD",
        "payment_terms": "Net 30",
        "purchase_order_number": "PO-2024-5678"
      },
      "confidence": 0.92,
      "processing_time": 12.5,
      "tokens_used": 245,
      "model": "mistral-7b-instruct-q4"
    }
  }
}
```

### Check Status (Failed)

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "status": "failed",
  "started_at": "2024-01-11T10:30:05",
  "completed_at": "2024-01-11T10:30:15",
  "error": "OCR failed: Tesseract not found. Install tesseract-ocr."
}
```

---

## Manual Correction

### Correct Extracted Fields

**Request:**
```http
POST /api/v1/documents/correct/doc_a1b2c3d4e5f6
Content-Type: application/json

{
  "corrections": {
    "invoice_number": "INV-2024-001",
    "vendor_name": "ACME Corporation Inc.",
    "total_amount": 5696.25
  },
  "notes": "Corrected OCR errors and vendor name variation"
}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "message": "Corrections applied successfully",
  "corrected_fields": [
    "invoice_number",
    "vendor_name",
    "total_amount"
  ]
}
```

---

## Validation

### Validate Extraction

**Request:**
```http
POST /api/v1/documents/validate/doc_a1b2c3d4e5f6
Content-Type: application/json

{
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "total_amount": 5696.25,
    "currency": "USD"
  }
}
```

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "is_valid": true,
  "errors": [],
  "warnings": [],
  "confidence_score": 0.95
}
```

### Validation Errors

**Response (200 OK):**
```json
{
  "document_id": "doc_a1b2c3d4e5f6",
  "is_valid": false,
  "errors": [
    {
      "field": "invoice_number",
      "error_message": "Missing required field"
    },
    {
      "field": "total_amount",
      "error_message": "Invalid format - must be numeric"
    }
  ],
  "warnings": [
    {
      "field": "due_date",
      "error_message": "Due date is in the past"
    }
  ],
  "confidence_score": 0.45
}
```

---

## Export & Download

### Export as JSON

**Request:**
```http
POST /api/v1/documents/export/doc_a1b2c3d4e5f6
Content-Type: application/json

{
  "format": "json",
  "include_ocr": true,
  "include_layout": false
}
```

**Response (200 OK):**
```
Content-Type: application/json
Content-Disposition: attachment; filename="doc_a1b2c3d4e5f6_export.json"

{
  "document_id": "doc_a1b2c3d4e5f6",
  "extraction": {
    "data": {...},
    "confidence": 0.92
  },
  "ocr": {
    "full_text": "...",
    "confidence": 0.87
  }
}
```

### Export as CSV

**Request:**
```http
POST /api/v1/documents/export/doc_a1b2c3d4e5f6
Content-Type: application/json

{
  "format": "csv",
  "include_ocr": false,
  "include_layout": false
}
```

**Response (200 OK):**
```
Content-Type: text/csv
Content-Disposition: attachment; filename="doc_a1b2c3d4e5f6_export.csv"

Field,Value
invoice_number,INV-2024-001
invoice_date,2024-01-08
due_date,2024-02-08
vendor_name,ACME Corporation
total_amount,5696.25
currency,USD
```

---

## Batch Processing

### Sequential Upload & Processing

```python
import requests
import time

API_BASE = "http://localhost:8000/api/v1"
documents = ["invoice1.pdf", "invoice2.pdf", "receipt.jpg"]

for doc in documents:
    # Upload
    with open(doc, "rb") as f:
        response = requests.post(
            f"{API_BASE}/documents/upload",
            files={"file": f},
            params={"document_type": "invoice"}
        )
    
    doc_id = response.json()["document_id"]
    print(f"Uploaded: {doc_id}")
    
    # Poll for completion
    while True:
        status = requests.get(
            f"{API_BASE}/documents/status/{doc_id}"
        ).json()
        
        if status["status"] == "completed":
            print(f"✓ {doc} processed")
            print(f"  Extracted: {len(status['result']['extraction']['data'])} fields")
            break
        elif status["status"] == "failed":
            print(f"✗ {doc} failed: {status['error']}")
            break
        
        time.sleep(5)
```

---

## Error Handling

### Document Not Found

**Response (404 Not Found):**
```json
{
  "error_code": "DOCUMENT_NOT_FOUND",
  "message": "Document not found: doc_invalid_id",
  "timestamp": "2024-01-11T10:40:00"
}
```

### Processing Still In Progress

**Response (400 Bad Request):**
```json
{
  "error_code": "PROCESSING_NOT_COMPLETE",
  "message": "Document not yet processed",
  "timestamp": "2024-01-11T10:40:00"
}
```

### Server Error

**Response (500 Internal Server Error):**
```json
{
  "error_code": "INTERNAL_ERROR",
  "message": "An internal error occurred",
  "details": {
    "error": "Tesseract crashed"
  },
  "timestamp": "2024-01-11T10:40:00"
}
```

---

## Rate Limiting & Timeouts

- Upload timeout: 30 seconds
- Processing timeout: 5 minutes
- Status check: 10 second timeout
- No rate limiting by default (can be added with middleware)

## Response Headers

All responses include:
```http
Content-Type: application/json
Access-Control-Allow-Origin: http://localhost:3000
Server: IDP/1.0.0
Date: [current timestamp]
```
