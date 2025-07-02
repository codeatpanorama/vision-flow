import os
import sys
import argparse
from pdf2image import convert_from_path
from dotenv import load_dotenv
from utils.logger import setup_logger

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger()

class PDFValidator:
    def __init__(self):
        pass
    
    def validate_pdf_images(self, pdf_path):
        """
        Validate that a PDF has an even number of images.
        
        Args:
            pdf_path (str): Path to the PDF file
            
        Returns:
            tuple: (is_valid, image_count, error_message)
        """
        try:
            # Check if file exists
            if not os.path.exists(pdf_path):
                return False, 0, f"PDF file not found: {pdf_path}"
            
            # Convert PDF to images
            logger.info(f"Converting PDF to images: {pdf_path}")
            images = convert_from_path(pdf_path)
            
            image_count = len(images)
            logger.info(f"Found {image_count} images in PDF")
            
            # Check if number of images is even
            if image_count % 2 != 0:
                error_msg = f"Invalid PDF: Found {image_count} images (odd number). Each check must have both front and back images."
                logger.error(error_msg)
                return False, image_count, error_msg
            
            logger.info(f"PDF validation successful: {image_count} images (even number)")
            return True, image_count, "PDF has valid number of images"
            
        except Exception as e:
            error_msg = f"Error validating PDF: {str(e)}"
            logger.error(error_msg)
            return False, 0, error_msg

def main():
    parser = argparse.ArgumentParser(description='Validate PDF file for check processing.')
    parser.add_argument('pdf_path', help='Path to the PDF file to validate')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level based on verbose flag
    if args.verbose:
        logger.setLevel('DEBUG')
    
    validator = PDFValidator()
    is_valid, image_count, message = validator.validate_pdf_images(args.pdf_path)
    
    if is_valid:
        print(f"✅ VALIDATION PASSED: {message}")
        print(f"   Image count: {image_count}")
        sys.exit(0)
    else:
        print(f"❌ VALIDATION FAILED: {message}")
        if image_count > 0:
            print(f"   Image count: {image_count}")
        sys.exit(1)

if __name__ == "__main__":
    main() 