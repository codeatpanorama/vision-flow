# PDF Validation Script Usage

## Overview

The `validation_checks.py` script validates PDF files to ensure they have an even number of images, which is required for check processing (each check needs both front and back images).

## Usage

### Command Line Usage

```bash
# Basic validation
python src/validation_checks.py path/to/your/checks.pdf

# Verbose logging
python src/validation_checks.py path/to/your/checks.pdf --verbose

# Or with short flag
python src/validation_checks.py path/to/your/checks.pdf -v
```

### Programmatic Usage

```python
from src.validation_checks import PDFValidator

validator = PDFValidator()
is_valid, image_count, message = validator.validate_pdf_images("path/to/your/checks.pdf")

if is_valid:
    print(f"PDF is valid with {image_count} images")
else:
    print(f"PDF validation failed: {message}")
```

## Output Examples

### Valid PDF (Even number of images)
```
✅ VALIDATION PASSED: PDF has valid number of images
   Image count: 6
```

### Invalid PDF (Odd number of images)
```
❌ VALIDATION FAILED: Invalid PDF: Found 5 images (odd number). Each check must have both front and back images.
   Image count: 5
```

### File Not Found
```
❌ VALIDATION FAILED: PDF file not found: nonexistent.pdf
```

## Exit Codes

- `0`: Validation passed (even number of images)
- `1`: Validation failed (odd number of images or other errors)

## Integration with Check Processing

You can use this validation script before running the main check processing:

```bash
# First validate the PDF
python src/validation_checks.py checks.pdf

# If validation passes, process the checks
python src/process_checks.py checks.pdf
```

Or in a script:

```python
from src.validation_checks import PDFValidator
from src.process_checks import CheckProcessor

validator = PDFValidator()
processor = CheckProcessor()

# Validate first
is_valid, _, _ = validator.validate_pdf_images("checks.pdf")

if is_valid:
    # Process if valid
    processor.process_pdf("checks.pdf")
else:
    print("PDF validation failed - cannot process")
```

## Requirements

- `pdf2image` library for PDF to image conversion
- Same environment setup as the main check processing script 