import os
import sys
import logging
from datetime import datetime, timezone
from dotenv import load_dotenv
from process_checks import CheckProcessor
from base_service import BaseMongoService

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/check_processor.log'),
        logging.StreamHandler()
    ]
)

class CheckProcessorService(BaseMongoService):
    def __init__(self, mongo_uri=None, db_name=None):
        """Initialize MongoDB connection and check processor"""
        super().__init__(mongo_uri, db_name, "CheckProcessor")
        self.check_processor = CheckProcessor()

    def find_pending_tasks(self):
        """Find tasks with bank_checks category, NOT_STARTED status, and REPORT type"""
        return super().find_pending_tasks("REPORT", "bank_checks")

    def process_pdf_file(self, pdf_path):
        """Process PDF file using the existing CheckProcessor"""
        try:
            if not os.path.exists(pdf_path):
                return False, f"PDF file not found: {pdf_path}"
            
            # Use the existing process_pdf method
            success = self.check_processor.process_pdf(pdf_path)
            
            if success:
                return True, "PDF processing completed successfully"
            else:
                return False, "PDF processing failed"
            
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return False, f"Processing error: {str(e)}"

    def process_task(self, task):
        """Process a single REPORT task"""
        task_id = task["_id"]
        document_id = task["documentId"]
        
        self.logger.info(f"Processing REPORT task {task_id} for document {document_id}")
        
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
            
            # Process PDF
            success, message = self.process_pdf_file(pdf_path)
            
            # Prepare processing result
            processing_result = {
                "success": success,
                "message": message,
                "pdfPath": pdf_path,
                "processedAt": datetime.now(timezone.utc).isoformat()
            }

            # Update task status
            if success:
                self.update_task_status(task_id, "COMPLETED", processing_result)
                self.logger.info(f"Task {task_id} processed successfully")
                return True
            else:
                self.update_task_status(task_id, "FAILED", processing_result)
                self.logger.error(f"Task {task_id} processing failed: {message}")
                return False
                
        except Exception as e:
            error_msg = f"Error processing task {task_id}: {str(e)}"
            self.logger.error(error_msg)
            self.update_task_status(task_id, "FAILED", {"error": error_msg})
            return False

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Continuous MongoDB-based check processing service')
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
        processor = CheckProcessorService(args.mongo_uri, args.db_name)
        processor.run_continuous_process(args.poll_interval)
    except Exception as e:
        logging.error(f"Failed to start processing service: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 