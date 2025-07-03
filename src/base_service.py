import os
import time
import uuid
import logging
from datetime import datetime, timezone
from pymongo import MongoClient

class BaseMongoService:
    """Base class for MongoDB-based services"""
    
    def __init__(self, mongo_uri=None, db_name=None, service_name="BaseService"):
        """Initialize MongoDB connection"""
        self.service_name = service_name
        self.logger = logging.getLogger(f"{service_name}")
        
        try:
            # Use environment variables if not provided
            self.mongo_uri = mongo_uri or os.getenv('MONGO_URI', 'mongodb://localhost:27017/')
            self.db_name = db_name or os.getenv('MONGO_DB_NAME', 'pan-ocr')
            
            # Handle authentication if credentials are provided
            mongo_username = os.getenv('MONGO_USERNAME')
            mongo_password = os.getenv('MONGO_PASSWORD')
            
            # Check for password file (Docker secrets)
            mongo_password_file = os.getenv('MONGO_PASSWORD_FILE')
            if mongo_password_file and os.path.exists(mongo_password_file):
                with open(mongo_password_file, 'r') as f:
                    mongo_password = f.read().strip()
            
            if mongo_username and mongo_password:
                # Create authenticated connection string
                from urllib.parse import quote_plus
                auth_uri = self.mongo_uri.replace('mongodb://', f'mongodb://{quote_plus(mongo_username)}:{quote_plus(mongo_password)}@')+self.db_name
                self.client = MongoClient(auth_uri)
            else:
                self.client = MongoClient(self.mongo_uri)
                
            self.db = self.client[self.db_name]
            self.task_collection = self.db['task']
            self.file_document_collection = self.db['file_document']
            
            # Test connection
            self.client.admin.command('ping')
            self.logger.info(f"Successfully connected to MongoDB at {self.mongo_uri}")
            
        except Exception as e:
            self.logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def find_pending_tasks(self, task_type, document_category="bank_checks"):
        """Find pending tasks with specified criteria"""
        try:
            query = {
                "documentCategory": document_category,
                "type": task_type,
                "status": "NOT_STARTED"
            }
            
            tasks = list(self.task_collection.find(query))
            self.logger.info(f"Found {len(tasks)} pending {task_type} tasks")
            return tasks
            
        except Exception as e:
            self.logger.error(f"Error finding pending tasks: {str(e)}")
            return []

    def get_file_document(self, document_id):
        """Get file document by document ID"""
        try:
            file_doc = self.file_document_collection.find_one({"_id": document_id})
            if not file_doc:
                self.logger.error(f"File document not found for documentId: {document_id}")
                return None
            return file_doc
            
        except Exception as e:
            self.logger.error(f"Error getting file document: {str(e)}")
            return None

    def create_check_task(self, document_id, document_category="bank_checks", task_type="REPORT", status="NOT_STARTED"):
        """Create a check report task"""
        try:
            task = {
                "createdAt": datetime.now(timezone.utc),
                "updatedAt": datetime.now(timezone.utc),
                "_id": uuid.uuid4().hex,
                "documentId": document_id,
                "documentCategory": document_category,
                "type": task_type,
                "status": status
            }

            result = self.task_collection.insert_one(task)
            if result.inserted_id:
                self.logger.info(f"Created check report task for document {document_id}")
                return result.inserted_id
            else:
                self.logger.error(f"Failed to create check report task for document {document_id}")
                return None
            
        except Exception as e:
            self.logger.error(f"Error creating check report task: {str(e)}")
            return None

    def update_task_status(self, task_id, status, result=None):
        """Update task status and add results"""
        try:
            update_data = {
                "status": status,
                "updatedAt": datetime.now(timezone.utc)
            }
            
            if result:
                # Use different field names based on service type
                if self.service_name == "CheckValidator":
                    update_data["validationResult"] = result
                elif self.service_name == "CheckProcessor":
                    update_data["processingResult"] = result
                else:
                    update_data["result"] = result
            
            result_update = self.task_collection.update_one(
                {"_id": task_id},
                {"$set": update_data}
            )
            
            if result_update.modified_count > 0:
                self.logger.info(f"Updated task {task_id} status to {status}")
            else:
                self.logger.warning(f"No task updated for ID: {task_id}")
                
        except Exception as e:
            self.logger.error(f"Error updating task status: {str(e)}")

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
                self.logger.info(f"Updated file document {document_id} with number of checks: {numberOfChecks}")
            else:
                self.logger.warning(f"No file document updated for ID: {document_id}")
                
        except Exception as e:
            self.logger.error(f"Error updating file document: {str(e)}")

    def run_continuous_process(self, poll_interval=None, process_task_func=None):
        """Run continuous processing service"""
        # Use environment variable if not provided
        poll_interval = poll_interval or int(os.getenv('POLL_INTERVAL', '30'))
        self.logger.info(f"Starting continuous {self.service_name} (polling every {poll_interval} seconds)")
        
        try:
            while True:
                try:
                    # Find pending tasks (implemented by subclasses)
                    pending_tasks = self.find_pending_tasks()
                    
                    if pending_tasks:
                        self.logger.info(f"Processing {len(pending_tasks)} pending tasks")
                        
                        for task in pending_tasks:
                            try:
                                if process_task_func:
                                    process_task_func(task)
                                else:
                                    self.process_task(task)
                            except Exception as e:
                                self.logger.error(f"Error processing individual task: {str(e)}")
                                continue
                    else:
                        self.logger.debug("No pending tasks found")
                    
                    # Wait before next poll
                    time.sleep(poll_interval)
                    
                except KeyboardInterrupt:
                    self.logger.info("Received interrupt signal, shutting down...")
                    break
                except Exception as e:
                    self.logger.error(f"Error in continuous process loop: {str(e)}")
                    time.sleep(poll_interval)  # Continue despite errors
                    
        finally:
            self.client.close()
            self.logger.info("MongoDB connection closed")

    def process_task(self, task):
        """Process a single task - to be implemented by subclasses"""
        raise NotImplementedError("Subclasses must implement process_task method") 