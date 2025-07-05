import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from validation_checks import PDFValidator
from base_service import BaseMongoService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/check_validator.log'),
        logging.StreamHandler()
    ]
)

class CheckValidator(BaseMongoService):
    def __init__(self, mongo_uri=None, db_name=None):
        """Initialize MongoDB connection and validator"""
        super().__init__(mongo_uri, db_name, "CheckValidator")
        self.validator = PDFValidator()

    def find_pending_tasks(self):
        """Find tasks with bank_checks category and NOT_STARTED status"""
        return super().find_pending_tasks("VALIDATE", "bank_checks")

    def validate_pdf_file(self, pdf_path):
        """Validate PDF file using the existing validator"""
        try:
            if not os.path.exists(pdf_path):
                return False, 0, f"PDF file not found: {pdf_path}"
            
            is_valid, image_count, message = self.validator.validate_pdf_images(pdf_path)
            return is_valid, image_count, message
            
        except Exception as e:
            self.logger.error(f"Error validating PDF: {str(e)}")
            return False, 0, f"Validation error: {str(e)}"

    def process_task(self, task):
        """Process a single validation task"""
        task_id = task["_id"]
        document_id = task["documentId"]
        
        self.logger.info(f"Processing task {task_id} for document {document_id}")

        # update task status
        self.update_task_status(task_id, "IN_PROGRESS", {"message": "Validating PDF"})
        
        try:
            # Get file document
            file_doc = self.get_file_document(document_id)
            if not file_doc:
                self.update_task_status(task_id, "FAILED", {"error": "File document not found"})
                return False
            
            # Get PDF path
            pdf_path = file_doc.get("path")
            if not pdf_path:
                self.update_task_status(task_id, "FAILED", {"error": "PDF path not found in file document"})
                return False
            
            # Validate PDF
            is_valid, image_count, message = self.validate_pdf_file(pdf_path)
            
            # Prepare validation result
            validation_result = {
                "isValid": is_valid,
                "imageCount": image_count,
                "message": message,
                "pdfPath": pdf_path,
                "validatedAt": datetime.now(timezone.utc).isoformat()
            }

            # Update task status
            if is_valid:
                self.update_task_status(task_id, "COMPLETED", validation_result)
                self.create_check_task(document_id, document_category="bank_checks", task_type="REPORT", status="NOT_STARTED")
                
                # Update the file document collection with number of checks 
                self.update_file_document(document_id, image_count//2)
                self.logger.info(f"Task {task_id} validated successfully: {image_count} images")
                return True
            else:
                self.update_task_status(task_id, "VALIDATION_FAILED", validation_result)
                self.logger.error(f"Task {task_id} validation failed: {message}")
                return False
                
        except Exception as e:
            error_msg = f"Error processing task {task_id}: {str(e)}"
            self.logger.error(error_msg)
            self.update_task_status(task_id, "FAILED", {"error": error_msg})
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Continuous MongoDB-based PDF validation process')
    parser.add_argument('--mongo-uri', 
                       help='MongoDB connection URI (overrides MONGO_URI env var)')
    parser.add_argument('--db-name', 
                       help='MongoDB database name (overrides MONGO_DB_NAME env var)')
    parser.add_argument('--poll-interval', type=int, 
                       help='Polling interval in seconds (overrides POLL_INTERVAL env var)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set log level
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    if args.verbose:
        log_level = 'DEBUG'
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    try:
        validator = CheckValidator(args.mongo_uri, args.db_name)
        validator.run_continuous_process(args.poll_interval)
    except Exception as e:
        logging.error(f"Failed to start validation process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 