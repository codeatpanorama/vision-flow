import os
import sys
import time
import logging
from datetime import datetime, timezone
from pymongo import MongoClient
from dotenv import load_dotenv
from validation_checks import PDFValidator

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/mongo_validator.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class MongoValidator:
    def __init__(self, mongo_uri=None, db_name=None):
        """Initialize MongoDB connection and validator"""
        try:
            # Use environment variables if not provided
            self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            self.db_name = db_name or os.getenv('MONGO_DB_NAME', 'pan-ocr')
            
            # Handle authentication if credentials are provided
            mongo_username = os.getenv('MONGO_USERNAME')
            print(f"MONGO_USERNAME: {mongo_username}")
            mongo_password = os.getenv('MONGO_PASSWORD')
            
            # Check for password file (Docker secrets)
            mongo_password_file = os.getenv('MONGO_PASSWORD_FILE')
            if mongo_password_file and os.path.exists(mongo_password_file):
                with open(mongo_password_file, 'r') as f:
                    mongo_password = f.read().strip()
            
            print(f"MONGO_PASSWORD: {mongo_password}")
            if mongo_username and mongo_password:
                # Create authenticated connection string
                from urllib.parse import quote_plus
                auth_uri = self.mongo_uri.replace('mongodb://', f'mongodb://{quote_plus(mongo_username)}:{quote_plus(mongo_password)}@')+self.db_name
                print(f"auth_uri: {auth_uri}")
                self.client = MongoClient(auth_uri)
            else:
                self.client = MongoClient(self.mongo_uri)
        
            self.db = self.client[self.db_name]
            self.task_collection = self.db['task']
            self.file_document_collection = self.db['file_document']
            self.validator = PDFValidator()
            
            # Test connection
            self.client.admin.command('ping')
            logger.info(f"Successfully connected to MongoDB at {self.mongo_uri}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def find_pending_tasks(self):
        """Find tasks with bank_checks category and NOT_STARTED status"""
        try:
            query = {
                "documentCategory": "bank_checks",
                "type": "VALIDATE",
                "status": "NOT_STARTED"
            }
            
            tasks = list(self.task_collection.find(query))
            logger.info(f"Found {len(tasks)} pending bank_checks tasks")
            return tasks
            
        except Exception as e:
            logger.error(f"Error finding pending tasks: {str(e)}")
            return []

    def get_file_document(self, document_id):
        """Get file document by document ID"""
        try:
            file_doc = self.file_document_collection.find_one({"_id": document_id})
            if not file_doc:
                logger.error(f"File document not found for documentId: {document_id}")
                return None
            return file_doc
            
        except Exception as e:
            logger.error(f"Error getting file document: {str(e)}")
            return None

    def update_task_status(self, task_id, status, validation_result=None):
        """Update task status and add validation results"""
        try:
            update_data = {
                "status": status,
                "updatedAt": datetime.now(timezone.utc)
            }
            
            if validation_result:
                update_data["validationResult"] = validation_result
            
            result = self.task_collection.update_one(
                {"_id": task_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated task {task_id} status to {status}")
            else:
                logger.warning(f"No task updated for ID: {task_id}")
                
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")

    def update_file_document(self, document_id, numberOfChecks):
        """Update the file document collection with number of checks"""
        try:
            update_data = {
                "numberOfChecks": numberOfChecks,
                "updatedAt": datetime.now(timezone.utc)
            }
            
            result = self.file_document_collection.update_one(
                {"_id": document_id},
                {"$set": update_data}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated file document {document_id} with number of checks: {numberOfChecks}")
            else:
                logger.warning(f"No file document updated for ID: {document_id}")
                
        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")

    def validate_pdf_file(self, pdf_path):
        """Validate PDF file using the existing validator"""
        try:
            if not os.path.exists(pdf_path):
                return False, 0, f"PDF file not found: {pdf_path}"
            
            is_valid, image_count, message = self.validator.validate_pdf_images(pdf_path)
            return is_valid, image_count, message
            
        except Exception as e:
            logger.error(f"Error validating PDF: {str(e)}")
            return False, 0, f"Validation error: {str(e)}"

    def process_task(self, task):
        """Process a single validation task"""
        task_id = task["_id"]
        document_id = task["documentId"]
        
        logger.info(f"Processing task {task_id} for document {document_id}")
        
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

                # Update the file document collection with number of checks 
                self.update_file_document(document_id, image_count//2)
                logger.info(f"Task {task_id} validated successfully: {image_count} images")
                return True
            else:
                self.update_task_status(task_id, "VALIDATION_FAILED", validation_result)
                logger.error(f"Task {task_id} validation failed: {message}")
                return False
                
        except Exception as e:
            error_msg = f"Error processing task {task_id}: {str(e)}"
            logger.error(error_msg)
            self.update_task_status(task_id, "FAILED", {"error": error_msg})
            return False

    def run_continuous_process(self, poll_interval=None):
        """Run continuous validation process"""
        # Use environment variable if not provided
        poll_interval = poll_interval or int(os.getenv('POLL_INTERVAL', '30'))
        logger.info(f"Starting continuous validation process (polling every {poll_interval} seconds)")
        
        try:
            while True:
                try:
                    # Find pending tasks
                    pending_tasks = self.find_pending_tasks()
                    
                    if pending_tasks:
                        logger.info(f"Processing {len(pending_tasks)} pending tasks")
                        
                        for task in pending_tasks:
                            try:
                                self.process_task(task)
                            except Exception as e:
                                logger.error(f"Error processing individual task: {str(e)}")
                                continue
                    else:
                        logger.debug("No pending tasks found")
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error in continuous process loop: {str(e)}")
                    time.sleep(poll_interval)  # Continue despite errors
                    
        finally:
            self.client.close()
            logger.info("MongoDB connection closed")

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
        validator = MongoValidator(args.mongo_uri, args.db_name)
        validator.run_continuous_process(args.poll_interval)
    except Exception as e:
        logger.error(f"Failed to start validation process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 