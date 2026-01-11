# 🗺️ IDP System - Project Navigation Guide

## 📚 Where to Start

### 👤 **For Users**
1. **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup and first use
2. **[README.md](README.md)** - Complete documentation
3. **[examples/API_EXAMPLES.md](examples/API_EXAMPLES.md)** - API usage examples
4. Open [http://localhost:8000/ui](http://localhost:8000/ui) - Web interface

### 👨‍💻 **For Developers**
1. **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Architecture overview
2. **[DELIVERABLES.md](DELIVERABLES.md)** - What's included
3. **[backend/app/main.py](backend/app/main.py)** - Start with main app
4. **[backend/app/services.py](backend/app/services.py)** - Processing logic
5. Check inline code comments and docstrings

### 🔧 **For Operations**
1. **[QUICKSTART.md](QUICKSTART.md)** - Initial setup
2. **[examples/CONFIGURATION.md](examples/CONFIGURATION.md)** - Configuration guide
3. **[README.md#Production](README.md#deployment)** - Production deployment
4. **[setup.sh](setup.sh)** - Automated setup

### 📝 **For API Integration**
1. **[examples/API_EXAMPLES.md](examples/API_EXAMPLES.md)** - Full API reference
2. **[examples/example_usage.py](examples/example_usage.py)** - Python client
3. **[http://localhost:8000/docs](http://localhost:8000/docs)** - Interactive API docs (after starting server)
4. **[backend/app/models/schemas.py](backend/app/models/schemas.py)** - Request/response models

---

## 📁 Directory Structure Guide

### **backend/** - FastAPI Application
```
backend/
├── app/
│   ├── main.py              ← Start here (FastAPI app setup)
│   ├── services.py          ← Core processing logic
│   ├── models/
│   │   └── schemas.py       ← Request/response models (Pydantic)
│   └── routers/
│       └── documents.py     ← All API endpoints
└── __init__.py
```

**Key Files:**
- [main.py](backend/app/main.py) - FastAPI app, middleware, routes
- [services.py](backend/app/services.py) - Document processing orchestration
- [documents.py](backend/app/routers/documents.py) - 7 REST endpoints

### **inference/** - Processing Pipeline
```
inference/
├── ocr/                     ← Tesseract & PaddleOCR
│   ├── engine.py           ← Text extraction
│   └── preprocessor.py     ← Image optimization
├── layout/                  ← Structure extraction
│   └── analyzer.py         ← Regions, tables, key-value pairs
└── llm/                     ← Local LLM inference
    └── engine.py           ← llama.cpp wrapper
```

**Processing Flow:**
1. [preprocessor.py](inference/ocr/preprocessor.py) - Image preprocessing
2. [engine.py (ocr)](inference/ocr/engine.py) - OCR extraction
3. [analyzer.py](inference/layout/analyzer.py) - Layout analysis
4. [engine.py (llm)](inference/llm/engine.py) - LLM extraction

### **config/** - Configuration
```
config/
├── settings.py              ← Environment variables & defaults
├── schemas.json             ← JSON schemas (invoice, receipt, form)
└── prompts.py              ← LLM prompt templates
```

**Configuration:**
- [settings.py](config/settings.py) - 40+ configuration options
- [schemas.json](config/schemas.json) - Document type schemas
- [prompts.py](config/prompts.py) - LLM prompts for each document type

### **ui/** - Web Interface
```
ui/
├── templates/
│   └── index.html          ← Single page web app
└── static/                 ← CSS/JS (future)
```

**Features:**
- [index.html](ui/templates/index.html) - Complete web UI with no external dependencies

### **examples/** - Documentation & Code
```
examples/
├── example_usage.py         ← Python API client
├── API_EXAMPLES.md         ← 20+ API examples
└── CONFIGURATION.md        ← Configuration examples
```

---

## 📖 Documentation Map

| Document | Purpose | For Whom |
|----------|---------|----------|
| **[QUICKSTART.md](QUICKSTART.md)** | 5-minute setup | Everyone |
| **[README.md](README.md)** | Complete guide | Everyone |
| **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** | Architecture overview | Developers |
| **[DELIVERABLES.md](DELIVERABLES.md)** | Feature checklist | Project managers |
| **[examples/API_EXAMPLES.md](examples/API_EXAMPLES.md)** | API reference | API users |
| **[examples/CONFIGURATION.md](examples/CONFIGURATION.md)** | Config guide | DevOps/Ops |
| **[examples/example_usage.py](examples/example_usage.py)** | Python examples | Python devs |

---

## 🔑 Key Concepts

### Processing Pipeline
```
Document Upload
    ↓
Image Preprocessing (deskew, denoise, binarize)
    ↓
OCR (Tesseract/PaddleOCR) → Text + Bounding Boxes
    ↓
Layout Analysis → Regions, Tables, Key-Value Pairs
    ↓
LLM Extraction (llama.cpp) → Structured JSON
    ↓
Validation → Confidence Scoring
    ↓
Export (JSON/CSV)
```

### API Response Flow
```
Upload → Document ID
  ↓
Start Processing → Background Task
  ↓
Poll Status → Processing/Completed/Failed
  ↓
Get Results → OCR, Layout, Extraction
  ↓
Correct Fields → Manual corrections
  ↓
Validate → Business rules
  ↓
Export → JSON/CSV
```

### Configuration Hierarchy
```
Default (hardcoded) ← Overridden by
    ↓
Environment Variables ← Set via
    ↓
.env File or System Environment
```

---

## 🚀 Common Tasks

### Run the System
```bash
source venv/bin/activate
python -m uvicorn backend.app.main:app --reload
```
👉 [See QUICKSTART.md](QUICKSTART.md)

### Upload a Document
```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@document.pdf" \
  -F "document_type=invoice"
```
👉 [See API_EXAMPLES.md](examples/API_EXAMPLES.md)

### Check Processing Status
```bash
curl http://localhost:8000/api/v1/documents/status/doc_abc123
```
👉 [See API_EXAMPLES.md](examples/API_EXAMPLES.md)

### Configure OCR Engine
Edit `.env`:
```env
OCR_ENGINE=tesseract  # or paddleocr
TESSERACT_PATH=/usr/bin/tesseract
```
👉 [See CONFIGURATION.md](examples/CONFIGURATION.md)

### Configure LLM Model
Edit `.env`:
```env
LLM_MODEL_PATH=/models/mistral-7b-instruct-q4.gguf
LLM_N_THREADS=4
LLM_TEMPERATURE=0.1
```
👉 [See CONFIGURATION.md](examples/CONFIGURATION.md)

### Deploy with Docker
```bash
docker-compose up -d
```
👉 [See README.md#Docker](README.md#deployment)

### Write Custom JSON Schema
Edit `config/schemas.json` or provide via API

### Integrate via Python
```python
from examples.example_usage import IDPClient
client = IDPClient()
response = client.upload_document("file.pdf", "invoice")
```
👉 [See example_usage.py](examples/example_usage.py)

---

## 🎯 Feature Locations

| Feature | Location | Documentation |
|---------|----------|----------------|
| **REST API** | [backend/app/routers/documents.py](backend/app/routers/documents.py) | [API_EXAMPLES.md](examples/API_EXAMPLES.md) |
| **Web UI** | [ui/templates/index.html](ui/templates/index.html) | [README.md#Web Application](README.md) |
| **Tesseract OCR** | [inference/ocr/engine.py](inference/ocr/engine.py) | [README.md#OCR](README.md) |
| **PaddleOCR** | [inference/ocr/engine.py](inference/ocr/engine.py) | [README.md#OCR](README.md) |
| **Image Preprocessing** | [inference/ocr/preprocessor.py](inference/ocr/preprocessor.py) | [README.md#Preprocessing](README.md) |
| **Layout Detection** | [inference/layout/analyzer.py](inference/layout/analyzer.py) | [README.md#Layout](README.md) |
| **LLM Inference** | [inference/llm/engine.py](inference/llm/engine.py) | [README.md#LLM](README.md) |
| **Configuration** | [config/settings.py](config/settings.py) | [CONFIGURATION.md](examples/CONFIGURATION.md) |
| **JSON Schemas** | [config/schemas.json](config/schemas.json) | [README.md#Schemas](README.md) |
| **Prompts** | [config/prompts.py](config/prompts.py) | [README.md#Prompting](README.md) |

---

## 🔧 Troubleshooting Guide

| Issue | Solution | Location |
|-------|----------|----------|
| Tesseract not found | Install system package | [QUICKSTART.md#Troubleshooting](QUICKSTART.md#troubleshooting) |
| LLM model not found | Download and set path | [CONFIGURATION.md](examples/CONFIGURATION.md) |
| Slow processing | Adjust settings | [CONFIGURATION.md](examples/CONFIGURATION.md) |
| Out of memory | Use smaller model | [README.md#Troubleshooting](README.md#troubleshooting) |
| API errors | Check health endpoint | [API_EXAMPLES.md](examples/API_EXAMPLES.md) |

👉 [See README.md#Troubleshooting](README.md#troubleshooting)

---

## 📊 Quick Reference

### Configuration Parameters
👉 [config/settings.py](config/settings.py) - All 40+ parameters documented

### API Endpoints
👉 [backend/app/routers/documents.py](backend/app/routers/documents.py) - 7 endpoints

### JSON Schemas
👉 [config/schemas.json](config/schemas.json) - Invoice, receipt, form schemas

### LLM Prompts
👉 [config/prompts.py](config/prompts.py) - Document-specific prompts

### Pydantic Models
👉 [backend/app/models/schemas.py](backend/app/models/schemas.py) - All request/response models

---

## 🆘 Getting Help

1. **Quick answers**: Check QUICKSTART.md
2. **API usage**: See examples/API_EXAMPLES.md
3. **Configuration**: See examples/CONFIGURATION.md
4. **Full docs**: See README.md
5. **Code**: Check inline comments and docstrings
6. **Errors**: Run with `DEBUG=true` and `LOG_LEVEL=DEBUG`

---

## ✅ Project Status

- ✅ Complete implementation
- ✅ Fully documented
- ✅ Production-ready
- ✅ Automated setup
- ✅ Example configurations
- ✅ Full API reference
- ✅ Web UI included

**Ready to deploy!** 🚀

---

**Last Updated**: 2024-01-11 | **Version**: 1.0.0
