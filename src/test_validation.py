#!/usr/bin/env python3
"""
Test script for validation_checks.py
Demonstrates how to use the PDF validation functionality.
"""

import sys
from pathlib import Path
from validation_checks import PDFValidator

def test_validation():
    """Test the PDF validation functionality"""
    
    # Add the src directory to the path so we can import modules
    src_path = Path(__file__).parent
    sys.path.insert(0, str(src_path))
    
    validator = PDFValidator()
    
    # Test with a sample PDF path (you would replace this with actual PDF path)
    test_pdf_path = "test_data/sample_checks.pdf"  # Replace with actual path
    
    print("Testing PDF validation...")
    print(f"PDF path: {test_pdf_path}")
    
    is_valid, image_count, message = validator.validate_pdf_images(test_pdf_path)
    
    print(f"\nValidation result:")
    print(f"  Valid: {is_valid}")
    print(f"  Image count: {image_count}")
    print(f"  Message: {message}")
    
    if is_valid:
        print("\n✅ PDF is ready for processing!")
    else:
        print("\n❌ PDF validation failed - cannot proceed with processing")

if __name__ == "__main__":
    test_validation() 