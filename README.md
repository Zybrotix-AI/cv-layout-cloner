# CV Layout Cloner

**Your content. Their design.** Upload your CV and a sample CV — get your content re-rendered in the sample's exact layout.

## Features

- **Three Fidelity Tiers**:
  - 🟢 **Tier 1 (Exact Match)** — Sample is `.docx`: literal run-text replacement preserving all formatting
  - 🟡 **Tier 2 (Near-Exact)** — Sample is text-based PDF: span redaction & reinsertion at original coordinates
  - 🔵 **Tier 3 (Best-Effort)** — Sample is image/scanned: AI-powered visual layout reconstruction

- **Multi-format input**: Accepts `.docx`, `.pdf`, `.png`, `.jpg` for both content and template CVs
- **Dual output**: Downloads in both `.docx` and `.pdf`
- **AI-powered**: Uses Claude API for semantic content extraction, template classification, and vision analysis
- **Live preview**: See your result before downloading

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Frontend** | React + Vite + Tailwind CSS v3 |
| **Backend** | FastAPI (Python 3.11) |
| **AI** | Anthropic Claude API (Sonnet for text, Opus for vision) |
| **Doc Processing** | python-docx, PyMuPDF, pdfplumber, pytesseract |
| **PDF Generation** | LibreOffice headless (Tier 1/2), Playwright (Tier 3) |
| **Container** | Docker + Docker Compose |

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Anthropic API key

### 1. Clone & Configure

```bash
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Run with Docker Compose

```bash
docker-compose up --build
```

- Frontend: http://localhost:1111
- Backend API: http://localhost:2222
- API Docs: http://localhost:2222/docs

### Local Development (without Docker)

#### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt

# System dependencies (required):
# - LibreOffice (for docx→pdf): sudo apt install libreoffice-writer
# - Tesseract OCR: sudo apt install tesseract-ocr
# - Playwright: playwright install chromium

cp .env.example .env
# Edit .env with your API key

uvicorn app.main:app --reload --port 2222
```

#### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Architecture

```
User uploads 2 files
    ↓
File Type Detection → determines Fidelity Tier
    ↓
Content Extraction (user's CV → canonical JSON via Claude)
    ↓
Template Analysis (sample CV → template map via Claude)
    ↓
Mapping (content fields → template slots by semantic role)
    ↓
Tier-specific Rendering:
  • Tier 1: Direct docx XML editing → LibreOffice PDF
  • Tier 2: PDF span redaction/reinsertion → PyMuPDF
  • Tier 3: HTML/CSS reconstruction → Playwright PDF
    ↓
Output: .docx + .pdf + preview image
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/convert` | Upload 2 CVs → get converted output |
| `GET` | `/api/download/{job_id}/{filename}` | Download output files |
| `GET` | `/api/health` | Health check with dependency status |

## License

MIT
