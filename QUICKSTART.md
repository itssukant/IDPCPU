# QUICK START GUIDE

## 5-Minute Setup

### Prerequisites
- Python 3.10+
- `pip` and `venv`
- ~10GB disk space (for models)

### Installation

1. **Clone/Navigate to project:**
   ```bash
   cd /path/to/IDPCPU
   ```

2. **Run setup script:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```
   
   The script will:
   - Create virtual environment
   - Install Python dependencies
   - Download LLM model (optional)
   - Create configuration file
   - Test the installation

3. **Start the server:**
   ```bash
   source venv/bin/activate
   python -m uvicorn backend.app.main:app --reload
   ```

4. **Open web UI:**
   - Browser: http://localhost:8000/ui
   - API docs: http://localhost:8000/docs

## Manual Setup (if script doesn't work)

### 1. Environment Setup
```bash
# Create virtual environment
python3.10 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. System Dependencies

**macOS:**
```bash
brew install tesseract
```

**Ubuntu/Debian:**
```bash
sudo apt-get install tesseract-ocr libtesseract-dev
```

**Windows:**
Download from: https://github.com/UB-Mannheim/tesseract/wiki

### 3. Download LLM Model

Choose one model and download (~3-4GB):

**Option A: Mistral 7B (Recommended)**
```bash
mkdir -p /models
cd /models
wget https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.1-GGUF/resolve/main/mistral-7b-instruct-v0.1.Q4_K_M.gguf -O mistral-7b-q4.gguf
```

**Option B: Llama 2 7B**
```bash
wget https://huggingface.co/TheBloke/Llama-2-7b-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf -O llama-2-7b-q4.gguf
```

**Option C: TinyLlama (lightweight, ~1.1GB)**
```bash
wget https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf -O tinyllama-q4.gguf
```

### 4. Configure

Create `.env` file:
```bash
cp .env.example .env  # Or create new
```

Edit `.env` and set:
```env
LLM_MODEL_PATH=/models/mistral-7b-q4.gguf  # Path to downloaded model
UPLOAD_DIR=/tmp/idp_uploads
DEBUG=true  # Set to false in production
```

### 5. Start Server

```bash
python -m uvicorn backend.app.main:app --reload
```

Server starts at: `http://localhost:8000`

## First Test Document

### Using Web UI
1. Go to http://localhost:8000/ui
2. Click upload area
3. Select a PDF or image
4. Wait for processing
5. Review extracted data

### Using API

```bash
# Upload document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample.pdf" \
  -F "document_type=invoice"

# Note the document_id from response

# Check status
curl http://localhost:8000/api/v1/documents/status/doc_abc123xyz456

# Check health
curl http://localhost:8000/api/v1/documents/health
```

## Troubleshooting

### "Tesseract not found"
```bash
# Check if installed
which tesseract

# On macOS, add to .env
echo "TESSERACT_PATH=$(which tesseract)" >> .env
```

### "Model not found"
- Verify `LLM_MODEL_PATH` in `.env`
- Ensure file exists: `ls -lh /models/mistral-7b-q4.gguf`
- Check path is absolute, not relative

### Out of Memory
- Use smaller model (TinyLlama)
- Reduce `LLM_CONTEXT_TOKENS` in .env
- Reduce `LLM_N_THREADS`

### Slow Processing
- Reduce image size before upload
- Disable preprocessing: `DESKEW_ENABLED=false`
- Use Q4 quantization instead of Q5

## Configuration Cheat Sheet

```env
# Minimal working config
DEBUG=true
UPLOAD_DIR=/tmp/idp_uploads
LLM_MODEL_PATH=/models/mistral-7b-q4.gguf
ENABLE_OCR=true
ENABLE_LLM_EXTRACTION=true
```

```env
# High performance
DEBUG=false
LLM_N_THREADS=20
LLM_CONTEXT_TOKENS=4096
DESKEW_ENABLED=true
DENOISE_ENABLED=true
```

```env
# Low resource
DEBUG=false
OCR_ENGINE=paddleocr
LLM_MODEL_PATH=/models/tinyllama-q4.gguf
LLM_CONTEXT_TOKENS=512
LLM_N_THREADS=2
DESKEW_ENABLED=false
```

## Next Steps

1. ✅ **Server Running**: Verify with `curl http://localhost:8000/`
2. 📄 **Test Upload**: Upload sample document via web UI
3. 📊 **Check Results**: Review extracted data
4. 🔧 **Tune Settings**: Adjust `.env` for your use case
5. 📚 **Read Documentation**: See [README.md](README.md)
6. 💻 **Integrate API**: Use examples in [examples/](examples/)

## Common Commands

```bash
# Activate environment
source venv/bin/activate

# Run server (development)
python -m uvicorn backend.app.main:app --reload

# Run server (production)
gunicorn backend.app.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker

# Run tests
pytest tests/ -v

# Format code
black .

# Check code
flake8 .

# View logs
tail -f logs/*.log
```

## Getting Help

1. Check [README.md](README.md) for detailed documentation
2. Review [examples/API_EXAMPLES.md](examples/API_EXAMPLES.md) for API usage
3. Check [examples/CONFIGURATION.md](examples/CONFIGURATION.md) for settings
4. Run with `DEBUG=true` and `LOG_LEVEL=DEBUG` for verbose output
5. Health check: `curl http://localhost:8000/api/v1/documents/health`

---

**Ready to process documents!** 🎉

Start with the web UI or API examples and customize as needed.
