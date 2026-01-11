#!/bin/bash
# IDP System Quick Start Setup Script
# Automates initial setup and configuration

set -e

echo "======================================"
echo "IDP - Intelligent Document Processing"
echo "Quick Start Setup"
echo "======================================"
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install dependencies
echo ""
echo "Installing dependencies..."
pip install -r requirements.txt

# Download sample LLM model
echo ""
echo "LLM Model Setup"
echo "==============="
read -p "Download sample LLM model? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    mkdir -p /tmp/idp_models
    echo "Downloading Mistral 7B Quantized (Q4_K_M)..."
    echo "Note: This is a ~3.5GB file. Takes 5-15 minutes depending on connection."
    
    # Create a Python script to download with progress
    python3 << 'EOF'
import os
import requests
from pathlib import Path

model_url = "https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf"
model_dir = Path("/tmp/idp_models")
model_dir.mkdir(exist_ok=True)
model_path = model_dir / "mistral-7b-instruct-q4.gguf"

if model_path.exists():
    print(f"Model already exists at {model_path}")
else:
    try:
        print(f"Downloading from: {model_url}")
        response = requests.get(model_url, stream=True)
        total_size = int(response.headers.get('content-length', 0))
        
        with open(model_path, 'wb') as f:
            downloaded = 0
            for chunk in response.iter_content(chunk_size=1024*1024):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    percent = (downloaded / total_size) * 100 if total_size else 0
                    print(f"Progress: {downloaded/1024/1024:.1f}MB / {total_size/1024/1024:.1f}MB ({percent:.1f}%)")
        
        print(f"✓ Model downloaded to: {model_path}")
    except Exception as e:
        print(f"Failed to download: {e}")
        print("You can download manually from:")
        print(model_url)
EOF
fi

# Create .env file
echo ""
echo "Creating .env configuration..."
read -p "Use development configuration? (y/n) " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > .env << 'EOF'
# Development Configuration
DEBUG=true
LOG_LEVEL=DEBUG

HOST=0.0.0.0
PORT=8000

# File handling
UPLOAD_DIR=/tmp/idp_uploads
MAX_UPLOAD_SIZE_MB=100

# OCR Configuration
OCR_ENGINE=tesseract
OCR_LANGUAGE=eng

# LLM Configuration
LLM_MODEL_PATH=/tmp/idp_models/mistral-7b-instruct-q4.gguf
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
LOG_SUPPRESS_SENSITIVE_DATA=true
EOF
else
    cat > .env << 'EOF'
# Production Configuration
DEBUG=false
LOG_LEVEL=INFO

HOST=0.0.0.0
PORT=8000

# File handling
UPLOAD_DIR=/var/idp/uploads
MAX_UPLOAD_SIZE_MB=50

# OCR Configuration
OCR_ENGINE=tesseract
OCR_LANGUAGE=eng

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
LOG_SUPPRESS_SENSITIVE_DATA=true
EOF
fi

echo "✓ Configuration created (.env)"

# Install system dependencies (macOS/Linux)
echo ""
echo "System Dependencies"
echo "==================="
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "Detected Linux"
    read -p "Install Tesseract OCR via apt-get? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr libtesseract-dev
        echo "✓ Tesseract installed"
    fi
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Detected macOS"
    read -p "Install Tesseract OCR via Homebrew? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        brew install tesseract
        echo "✓ Tesseract installed"
    fi
else
    echo "Please install Tesseract manually from:"
    echo "https://github.com/UB-Mannheim/tesseract/wiki"
fi

# Create necessary directories
echo ""
echo "Creating directories..."
mkdir -p /tmp/idp_uploads
mkdir -p logs
mkdir -p data

# Test the installation
echo ""
echo "Testing installation..."
python3 << 'EOF'
import sys
from pathlib import Path

errors = []

# Check Python version
if sys.version_info < (3, 10):
    errors.append(f"Python 3.10+ required, found {sys.version_info.major}.{sys.version_info.minor}")

# Check imports
try:
    import fastapi
    print("✓ FastAPI installed")
except ImportError:
    errors.append("FastAPI not installed")

try:
    import cv2
    print("✓ OpenCV installed")
except ImportError:
    errors.append("OpenCV not installed")

try:
    import pytesseract
    print("✓ pytesseract installed")
except ImportError:
    print("⚠ pytesseract not installed (OCR may not work)")

try:
    from paddleocr import PaddleOCR
    print("✓ PaddleOCR available")
except ImportError:
    print("⚠ PaddleOCR not installed (alternative OCR unavailable)")

try:
    from llama_cpp import Llama
    print("✓ llama-cpp-python installed")
except ImportError:
    errors.append("llama-cpp-python not installed (LLM inference won't work)")

# Check model file
from config import settings
model_path = Path(settings.LLM_MODEL_PATH)
if model_path.exists():
    print(f"✓ LLM model found at {settings.LLM_MODEL_PATH}")
else:
    print(f"⚠ LLM model not found at {settings.LLM_MODEL_PATH}")
    print("  Download one and set LLM_MODEL_PATH in .env")

if errors:
    print("\n✗ Setup has issues:")
    for error in errors:
        print(f"  - {error}")
    sys.exit(1)
else:
    print("\n✓ Setup successful!")
EOF

# Prompt to start server
echo ""
echo "======================================"
echo "Setup Complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "1. Review configuration in .env"
echo "2. Start the server:"
echo "   python -m uvicorn backend.app.main:app --reload"
echo "3. Open browser:"
echo "   http://localhost:8000/ui"
echo "4. Try uploading a document"
echo ""
read -p "Start server now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python -m uvicorn backend.app.main:app --reload
fi
