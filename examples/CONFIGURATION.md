# Environment Configuration Examples

## Development Setup

Create `.env.dev`:
```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=true
LOG_LEVEL=DEBUG

# File handling
UPLOAD_DIR=/tmp/idp_uploads_dev
MAX_UPLOAD_SIZE_MB=100

# OCR Configuration
OCR_ENGINE=tesseract
OCR_LANGUAGE=eng
TESSERACT_PATH=/usr/bin/tesseract

# LLM Configuration
LLM_MODEL_PATH=/models/mistral-7b-instruct-q4.gguf
LLM_CONTEXT_TOKENS=2048
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.1
LLM_TOP_P=0.95
LLM_N_THREADS=4

# Processing Pipeline
ENABLE_OCR=true
ENABLE_LAYOUT_ANALYSIS=true
ENABLE_LLM_EXTRACTION=true
ENABLE_VALIDATION=true

# Logging
LOG_LEVEL=DEBUG
LOG_SUPPRESS_SENSITIVE_DATA=false
```

Usage:
```bash
# Development
export $(cat .env.dev | xargs) && python -m uvicorn backend.app.main:app --reload
```

## Production Setup

Create `.env.prod`:
```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false
LOG_LEVEL=WARNING

# File handling
UPLOAD_DIR=/var/idp/uploads
MAX_UPLOAD_SIZE_MB=50

# OCR Configuration
OCR_ENGINE=tesseract
OCR_LANGUAGE=eng
TESSERACT_PATH=/usr/bin/tesseract

# LLM Configuration
LLM_MODEL_PATH=/var/idp/models/mistral-7b-instruct-q4.gguf
LLM_CONTEXT_TOKENS=2048
LLM_MAX_TOKENS=512
LLM_TEMPERATURE=0.1  # Deterministic
LLM_TOP_P=0.95
LLM_N_THREADS=8

# Processing Pipeline
ENABLE_OCR=true
ENABLE_LAYOUT_ANALYSIS=true
ENABLE_LLM_EXTRACTION=true
ENABLE_VALIDATION=true

# Logging - Suppress sensitive data
LOG_LEVEL=INFO
LOG_SUPPRESS_SENSITIVE_DATA=true

# Database (optional)
DATABASE_URL=sqlite:////var/idp/idp.db
```

Usage:
```bash
# Production with Gunicorn
gunicorn backend.app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## CPU-Optimized Setup (Limited Resources)

For systems with 4GB RAM and 2-core CPU:

```env
# Server
HOST=127.0.0.1
PORT=8000
DEBUG=false

# File handling
UPLOAD_DIR=/tmp/idp_uploads
MAX_UPLOAD_SIZE_MB=20  # Smaller max file size

# OCR Configuration
OCR_ENGINE=paddleocr  # Lighter than Tesseract
OCR_LANGUAGE=en

# LLM Configuration - Lower resource usage
LLM_MODEL_PATH=/models/tinyllama-1.1b-chat-q4.gguf  # Tiny model
LLM_CONTEXT_TOKENS=512  # Reduce context
LLM_MAX_TOKENS=256  # Shorter output
LLM_TEMPERATURE=0.1
LLM_TOP_P=0.95
LLM_N_THREADS=2  # Match CPU cores

# Processing Pipeline
ENABLE_OCR=true
ENABLE_LAYOUT_ANALYSIS=true  # Lightweight
ENABLE_LLM_EXTRACTION=true
ENABLE_VALIDATION=true

# Logging
LOG_LEVEL=WARNING  # Reduce overhead
LOG_SUPPRESS_SENSITIVE_DATA=true

# Preprocessing (disable expensive operations)
DESKEW_ENABLED=false  # Skip deskew for speed
DENOISE_ENABLED=true
BINARIZATION_ENABLED=true

# Layout Detection (adjust thresholds)
MIN_TEXT_BLOCK_HEIGHT=20  # Larger minimum
MIN_TEXT_BLOCK_WIDTH=30
PROXIMITY_THRESHOLD=20
```

## High-Performance Setup (24-core CPU, 64GB RAM)

```env
# Server
HOST=0.0.0.0
PORT=8000
DEBUG=false

# File handling
UPLOAD_DIR=/fast_storage/idp_uploads  # NVMe SSD recommended
MAX_UPLOAD_SIZE_MB=500  # Large files

# OCR Configuration - Best quality
OCR_ENGINE=tesseract  # Higher accuracy
OCR_LANGUAGE=eng

# LLM Configuration - Larger model
LLM_MODEL_PATH=/models/mistral-7b-instruct-q5.gguf  # Higher quality quantization
LLM_CONTEXT_TOKENS=4096  # Larger context
LLM_MAX_TOKENS=1024  # Longer responses
LLM_TEMPERATURE=0.05  # More deterministic
LLM_TOP_P=0.90
LLM_N_THREADS=20  # Use most cores

# Processing Pipeline
ENABLE_OCR=true
ENABLE_LAYOUT_ANALYSIS=true
ENABLE_LLM_EXTRACTION=true
ENABLE_VALIDATION=true

# Preprocessing - All enabled
DESKEW_ENABLED=true
DENOISE_ENABLED=true
BINARIZATION_ENABLED=true

# Layout Detection (strict)
MIN_TEXT_BLOCK_HEIGHT=5
MIN_TEXT_BLOCK_WIDTH=10
PROXIMITY_THRESHOLD=10
TABLE_ROW_THRESHOLD=5

# Logging
LOG_LEVEL=INFO
LOG_SUPPRESS_SENSITIVE_DATA=true
```

## GPU Acceleration Setup (Not Recommended)

GPU support is not included in this offline system. However, if needed:

```env
# Use CPU only - this is the default
LLM_N_THREADS=4
```

All inference is CPU-based to ensure maximum compatibility and determinism.

## Docker Compose Example

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  idp-backend:
    image: idp-system:latest
    ports:
      - "8000:8000"
    environment:
      HOST: "0.0.0.0"
      PORT: "8000"
      DEBUG: "false"
      UPLOAD_DIR: "/data/uploads"
      LLM_MODEL_PATH: "/models/mistral-7b-instruct-q4.gguf"
      LLM_N_THREADS: "8"
    volumes:
      - ./models:/models:ro
      - ./uploads:/data/uploads
      - ./logs:/data/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/documents/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

Usage:
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f idp-backend

# Stop services
docker-compose down
```

## Configuration Options Reference

### Server
- `HOST`: Bind address (default: 0.0.0.0)
- `PORT`: Port number (default: 8000)
- `DEBUG`: Enable debug mode (default: false)
- `APP_NAME`: Application name
- `APP_VERSION`: Version string

### File Handling
- `UPLOAD_DIR`: Directory for uploaded files
- `MAX_UPLOAD_SIZE_MB`: Maximum upload size in MB
- `ALLOWED_EXTENSIONS`: Comma-separated file extensions

### OCR
- `OCR_ENGINE`: tesseract or paddleocr
- `OCR_LANGUAGE`: Language code (eng, fra, ...)
- `TESSERACT_PATH`: Path to tesseract binary
- `OCR_TIMEOUT_SECONDS`: Processing timeout

### Preprocessing
- `DESKEW_ENABLED`: Enable skew correction
- `DENOISE_ENABLED`: Enable noise reduction
- `BINARIZATION_ENABLED`: Enable binarization

### LLM
- `LLM_MODEL_PATH`: Path to GGUF model file
- `LLM_CONTEXT_TOKENS`: Context window size
- `LLM_MAX_TOKENS`: Max generation tokens
- `LLM_TEMPERATURE`: Sampling temperature (0.0-1.0)
- `LLM_TOP_P`: Nucleus sampling parameter
- `LLM_N_THREADS`: Number of CPU threads
- `LLM_TIMEOUT_SECONDS`: Processing timeout

### Processing Pipeline
- `ENABLE_OCR`: Enable OCR processing
- `ENABLE_LAYOUT_ANALYSIS`: Enable layout detection
- `ENABLE_LLM_EXTRACTION`: Enable LLM extraction
- `ENABLE_VALIDATION`: Enable validation

### Layout Detection
- `MIN_TEXT_BLOCK_HEIGHT`: Minimum block height
- `MIN_TEXT_BLOCK_WIDTH`: Minimum block width
- `PROXIMITY_THRESHOLD`: Pixels for region grouping
- `TABLE_ROW_THRESHOLD`: Table row detection gap

### Logging
- `LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR)
- `LOG_SUPPRESS_SENSITIVE_DATA`: Mask sensitive patterns

## Validation

To validate configuration:
```python
from config import settings

# Check all settings loaded
print(f"OCR Engine: {settings.OCR_ENGINE}")
print(f"LLM Model: {settings.LLM_MODEL_PATH}")
print(f"Upload Dir: {settings.UPLOAD_DIR}")
print(f"Debug: {settings.DEBUG}")

# Verify model file exists
from pathlib import Path
if Path(settings.LLM_MODEL_PATH).exists():
    print("✓ LLM model found")
else:
    print("✗ LLM model not found")
```
