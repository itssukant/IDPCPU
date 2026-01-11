# Intelligent Document Processing (IDP) System

An enterprise-grade, fully offline document processing system with built-in LLM inference. Designed for on-premises deployment with zero external dependencies.

## Features

✅ **Fully Offline & On-Premises**
- No external API calls
- No telemetry or analytics
- Suitable for air-gapped environments

✅ **Open Source Only**
- Tesseract OCR
- PaddleOCR
- llama.cpp for local inference
- FastAPI for backend
- OpenCV for image processing

✅ **CPU-Only Operation**
- No GPU requirements
- Quantized models for efficiency
- Suitable for cost-effective deployment

✅ **Deterministic Processing**
- Low temperature LLM inference
- No hallucination mode
- Strict JSON schema validation
- Rule-based layout extraction

✅ **Enterprise Features**
- Document upload and management
- Interactive web UI for review
- Manual field correction
- Validation and consistency checks
- Export to JSON/CSV

## Architecture

```
IDP System
├── Backend (FastAPI)
│   ├── Document Management
│   ├── Processing Orchestration
│   └── REST API
├── Inference Pipeline
│   ├── OCR Layer (Tesseract/PaddleOCR)
│   ├── Layout Extraction
│   └── LLM Inference (llama.cpp)
└── Web UI
    ├── Document Upload
    ├── Results Review
    └── Field Editing
```

## System Requirements

- **Python**: 3.10+
- **OS**: Linux, macOS, Windows
- **CPU**: 4+ cores recommended
- **RAM**: 8GB minimum (16GB+ recommended)
- **Disk**: 10GB+ for models and uploads

## Installation

### 1. Clone and Setup

```bash
cd /path/to/IDPCPU
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    python3-dev
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Download LLM Model

Download a quantized GGUF model (required for extraction):

```bash
# Create models directory
mkdir -p /models

# Download a model (e.g., Mistral 7B Quantized)
# ~3GB file
wget -O /models/mistral-7b-instruct-q4.gguf \
    https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf
```

**Recommended Models:**
- Mistral 7B Quantized (~3GB)
- Llama 2 7B Quantized (~3-4GB)
- Neural Chat 7B (~3GB)

Models should be:
- Quantized (Q4_0, Q4_K_M, or Q5 format)
- Around 3-7GB in size
- In GGUF format

## Configuration

Create a `.env` file in the project root:

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# File handling
UPLOAD_DIR=/tmp/idp_uploads
MAX_UPLOAD_SIZE_MB=50

# OCR Configuration
OCR_ENGINE=tesseract  # or paddleocr
OCR_LANGUAGE=eng
TESSERACT_PATH=/usr/bin/tesseract  # Optional

# LLM Configuration
LLM_MODEL_PATH=/models/mistral-7b-instruct-q4.gguf
LLM_CONTEXT_TOKENS=2048
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.1
LLM_TOP_P=0.95
LLM_N_THREADS=4  # Auto-detected if not set

# Processing Pipeline
ENABLE_OCR=true
ENABLE_LAYOUT_ANALYSIS=true
ENABLE_LLM_EXTRACTION=true
ENABLE_VALIDATION=true

# Logging
LOG_LEVEL=INFO
LOG_SUPPRESS_SENSITIVE_DATA=true
```

## Usage

### Start the Server

```bash
python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

Server will start at: `http://localhost:8000`

### Access Web UI

Open browser: `http://localhost:8000/ui`

### API Endpoints

#### Upload Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@invoice.pdf" \
  -F "document_type=invoice"
```

Response:
```json
{
  "document_id": "doc_abc123xyz456",
  "filename": "invoice.pdf",
  "document_type": "invoice",
  "size_bytes": 245600,
  "upload_timestamp": "2024-01-11T10:30:00",
  "status": "pending"
}
```

#### Check Processing Status
```bash
curl http://localhost:8000/api/v1/documents/status/doc_abc123xyz456
```

#### Manual Correction
```bash
curl -X POST http://localhost:8000/api/v1/documents/correct/doc_abc123xyz456 \
  -H "Content-Type: application/json" \
  -d '{
    "corrections": {
      "invoice_number": "INV-2024-001",
      "total_amount": 5250.00
    },
    "notes": "Fixed OCR errors"
  }'
```

#### Export Results
```bash
curl -X POST http://localhost:8000/api/v1/documents/export/doc_abc123xyz456 \
  -H "Content-Type: application/json" \
  -d '{"format": "json", "include_ocr": true}' \
  > results.json
```

#### Health Check
```bash
curl http://localhost:8000/api/v1/documents/health
```

## Processing Pipeline

### 1. Document Upload
- Validate file type and size
- Generate unique document ID
- Store in upload directory

### 2. Preprocessing
- Deskew image
- Denoise
- Binarization
- Optimize for OCR

### 3. OCR (Optical Character Recognition)
- Extract text and bounding boxes
- Use Tesseract or PaddleOCR
- Filter by confidence threshold
- Generate text blocks

### 4. Layout Analysis
- Group text blocks by spatial proximity
- Detect tables
- Extract key-value pairs
- Identify document structure

### 5. LLM Extraction
- Use quantized model for inference
- Deterministic extraction (temperature=0.1)
- Strict JSON schema validation
- No hallucination mode
- No inferred values

### 6. Validation
- Check against business rules
- Verify data consistency
- Confidence scoring
- Detect anomalies

### 7. Export
- JSON format
- CSV format
- Include OCR and layout if requested

## JSON Schema Examples

### Invoice Schema

```json
{
  "invoice_number": "INV-2024-001",
  "invoice_date": "2024-01-08",
  "due_date": "2024-02-08",
  "vendor_name": "ACME Corporation",
  "total_amount": 5250.00,
  "currency": "USD",
  "items": [
    {
      "description": "Professional Services",
      "quantity": 1,
      "unit_price": 5000.00,
      "total": 5000.00
    }
  ]
}
```

### Receipt Schema

```json
{
  "receipt_number": "REC-2024-001",
  "date_time": "2024-01-11T14:30:00",
  "merchant_name": "Coffee Shop ABC",
  "items": [
    {"item_name": "Espresso", "quantity": 1, "price": 2.50}
  ],
  "total": 2.50,
  "payment_method": "card"
}
```

## Development

### Project Structure

```
IDPCPU/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI app
│       ├── services.py       # Business logic
│       ├── models/
│       │   └── schemas.py    # Pydantic models
│       └── routers/
│           └── documents.py  # API routes
├── inference/
│   ├── ocr/                  # OCR engines
│   ├── layout/               # Layout analysis
│   └── llm/                  # LLM inference
├── ui/
│   ├── templates/
│   │   └── index.html        # Web UI
│   └── static/               # CSS, JS
├── config/
│   ├── settings.py           # Configuration
│   ├── schemas.json          # JSON schemas
│   └── prompts.py            # LLM prompts
└── examples/
    └── example_usage.py      # Usage examples
```

### Running Tests

```bash
pytest tests/ -v
```

### Code Standards

- **Format**: Black
- **Lint**: Flake8
- **Type hints**: Enabled
- **Docstrings**: Google style

## Troubleshooting

### OCR Not Working
- Verify Tesseract is installed: `which tesseract`
- Check `TESSERACT_PATH` in .env
- Ensure OCR engine is enabled: `ENABLE_OCR=true`

### LLM Model Not Loading
- Verify model file exists at `LLM_MODEL_PATH`
- Check file format (must be GGUF)
- Ensure sufficient disk space
- Try reducing context tokens if OOM errors

### Slow Processing
- Increase `LLM_N_THREADS` up to CPU count
- Use more aggressive quantization (Q4 vs Q8)
- Reduce `LLM_MAX_TOKENS`
- Enable `DESKEW_ENABLED=true` for preprocessing

### Memory Usage High
- Reduce `LLM_CONTEXT_TOKENS`
- Use Q4_K_M quantized models
- Process smaller batches
- Monitor with: `top` or `htop`

## Performance

Typical processing times (single document, 4-core CPU):

| Stage | Time | Notes |
|-------|------|-------|
| Upload | <1s | |
| Preprocessing | 2-5s | Image optimization |
| OCR | 5-30s | Depends on image quality |
| Layout Analysis | <1s | Deterministic |
| LLM Extraction | 10-60s | Model & inference |
| **Total** | **20-120s** | Typical: 30-60s |

Batch processing scales linearly. Use background tasks for better UX.

## Security Considerations

✅ **No External Connections**
- Verify with network monitoring
- Use in air-gapped networks

✅ **Data Handling**
- Models kept in `/models` directory
- Uploads in `/tmp/idp_uploads` (configurable)
- No data logging by default
- Optional sensitive data masking

✅ **Access Control**
- Add authentication layer for multi-user deployment
- Use firewall rules to restrict API access
- Run behind reverse proxy (nginx, etc.)

## Deployment

### Docker

```bash
docker build -t idp-system .
docker run -p 8000:8000 \
  -v /models:/models \
  -v /data:/tmp/idp_uploads \
  idp-system
```

### Production Checklist

- [ ] Set `DEBUG=false`
- [ ] Configure reverse proxy (nginx)
- [ ] Set up authentication
- [ ] Configure logging and monitoring
- [ ] Set upload size limits
- [ ] Use production-grade ASGI server
- [ ] Monitor system resources
- [ ] Regular model updates
- [ ] Backup configuration

## Contributing

Contributions welcome! Please ensure:
- Code follows Black formatting
- Type hints are present
- Docstrings are comprehensive
- Tests pass
- No external dependencies added without approval

## License

This system uses:
- Tesseract OCR (Apache 2.0)
- PaddleOCR (Apache 2.0)
- llama.cpp (MIT)
- FastAPI (MIT)
- OpenCV (Apache 2.0)

Ensure compliance with all open-source licenses.

## Support

For issues and questions:
1. Check troubleshooting section
2. Review logs: `LOG_LEVEL=DEBUG`
3. Run health check: `/api/v1/documents/health`
4. Verify configuration: Check `.env` file

## Roadmap

- [ ] Database support for job tracking
- [ ] Advanced table extraction
- [ ] Handwriting recognition
- [ ] Multi-language support improvement
- [ ] Quantized model optimization
- [ ] Web UI enhancements
- [ ] REST API v2 with batch operations
- [ ] WebSocket for real-time updates

---

**Last Updated**: 2024-01-11
**Version**: 1.0.0
