# OCR Extractor

A modern, well-structured PDF to text extraction pipeline using OCR API.

## 📋 Features

✅ Extract multiple PDF pages as images  
✅ Batch processing for multiple images  
✅ Preserve text formatting and structure  
✅ Markdown output with page references  
✅ Error handling and progress tracking  
✅ Support for multiple image formats (PNG, JPG, JPEG, GIF, WEBP)  
✅ Configurable via environment variables  
✅ Command-line interface with Click  
✅ Proper Python package structure  
✅ Comprehensive test suite  
✅ Document reconstruction (merge pages, remove artifacts)

## 🚀 Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if not already installed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Activate virtual environment
poetry shell
```

### Using pip

```bash
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Copy the example configuration:
```bash
cp .env.example .env
```

2. Edit `.env` with your API credentials:
```bash
# Required: Your OCR API key
OCR_API_KEY=your-api-key-here

# Optional: Customize other settings
OCR_BASE_URL=https://mkp-api.fptcloud.com
OCR_MODEL_NAME=gemma-3-27b-it
OCR_DPI=200
```

## 📖 Usage

### Command Line Interface

The package provides a modern CLI with the following commands:

#### Extract text from PDF (complete pipeline)
```bash
ocr-extract extract-pdf document.pdf
```

With custom output directory and file:
```bash
ocr-extract extract-pdf document.pdf --output-dir images --output-file result.md
```

With automatic document reconstruction:
```bash
ocr-extract extract-pdf document.pdf --reconstruct
```

#### Reconstruct document from extracted text
```bash
ocr-extract reconstruct extracted_text.md --output-file final_document.md
```

#### Extract text from images only
```bash
ocr-extract extract-images img/
```

Or from specific image files:
```bash
ocr-extract extract-images image1.png image2.jpg
```

#### Extract images from PDF (without OCR)
```bash
ocr-extract extract-images-only document.pdf
```

#### Get help
```bash
ocr-extract --help
ocr-extract extract-pdf --help
```

### Python API

```python
from ocr_extractor import PDFTextExtractor

# Initialize extractor
extractor = PDFTextExtractor()

# Process a PDF
results = extractor.process_pdf("document.pdf")

# Extract from images
from ocr_extractor.extractor import extract_text_from_images_batch
results = extract_text_from_images_batch(["img/page1.png", "img/page2.png"])
```

## 📁 Project Structure

```
ocr-extractor/
├── src/ocr_extractor/
│   ├── __init__.py
│   ├── cli.py          # Command-line interface
│   ├── config.py       # Configuration management
│   └── extractor.py    # Core extraction logic
├── tests/
│   ├── __init__.py
│   └── test_extractor.py
├── pyproject.toml      # Poetry configuration
├── .env.example        # Configuration template
├── .gitignore
└── README.md
```

## 🧪 Testing

Run the test suite:

```bash
poetry run pytest
```

## 📊 Output Format

```markdown
# Extracted Text from PDF

Total pages processed: 3

## Page 1: document_page_1.png

[Extracted text here...]

---

## Page 2: document_page_2.png

[Extracted text here...]
```

## 🔧 Development

### Setup development environment

```bash
poetry install --with dev
```

### Code formatting

```bash
poetry run black src/ tests/
poetry run isort src/ tests/
```

### Linting

```bash
poetry run flake8 src/ tests/
```

## 📋 Requirements

- Python 3.8+
- OCR API access (FPT Cloud or compatible)
- Poppler (for pdf2image)
- Poetry (for dependency management)

## 📄 License

[Add your license here]
