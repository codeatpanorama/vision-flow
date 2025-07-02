# Check Validator - MongoDB Continuous Validation Process

## Overview

The `check_validator.py` script runs a continuous process that polls MongoDB for bank check validation tasks and automatically validates PDF files.

## Environment Configuration

Create a `.env` file in the project root with your MongoDB configuration:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your settings
nano .env
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MONGO_URI` | MongoDB connection URI | `mongodb://localhost:27017/` |
| `MONGO_DB_NAME` | Database name | `pan-ocr` |
| `MONGO_USERNAME` | MongoDB username (optional) | - |
| `MONGO_PASSWORD` | MongoDB password (optional) | - |
| `POLL_INTERVAL` | Polling interval in seconds | `30` |
| `LOG_LEVEL` | Logging level (INFO, DEBUG, etc.) | `INFO` |

## How It Works

1. **Polls MongoDB** every 30 seconds (configurable) for tasks with:
   - `documentCategory`: "bank_checks"
   - `status`: "NOT_STARTED"

2. **Retrieves PDF path** from the `File_document` collection using the `documentId`

3. **Validates PDF** using the existing validation logic (checks for even number of images)

4. **Updates task status** in MongoDB with validation results

## Usage

### Basic Usage
```bash
# Start with environment variables (recommended)
python src/check_validator.py

# Override specific settings via command line
python src/check_validator.py --mongo-uri mongodb://localhost:27017/
python src/check_validator.py --db-name pan-ocr
python src/check_validator.py --poll-interval 60
python src/check_validator.py --verbose
```

### All Options
```bash
python src/check_validator.py \
  --mongo-uri mongodb://localhost:27017/ \
  --db-name pan-ocr \
  --poll-interval 30 \
  --verbose
```

## Task Status Updates

The process updates task documents with the following statuses:

- **`VALIDATED`**: PDF has even number of images
- **`VALIDATION_FAILED`**: PDF has odd number of images
- **`FAILED`**: Error occurred during processing

### Validation Result Structure
```json
{
  "isValid": true,
  "imageCount": 6,
  "message": "PDF has valid number of images",
  "pdfPath": "repository/bank_checks/...",
  "validatedAt": "2025-01-02T10:30:00.000Z"
}
```

## Logging

- **Console output**: Real-time validation status
- **File logging**: `logs/mongo_validator.log`
- **Log levels**: INFO (default), DEBUG (with --verbose)

## Example Log Output

```
2025-01-02 10:30:00 - INFO - Successfully connected to MongoDB at mongodb://localhost:27017/
2025-01-02 10:30:00 - INFO - Starting continuous validation process (polling every 30 seconds)
2025-01-02 10:30:00 - INFO - Found 2 pending bank_checks tasks
2025-01-02 10:30:00 - INFO - Processing task ee73a218-6292-43e3-9052-f495745aa646 for document 8cda5327-332a-4c00-9d71-725f7e750305
2025-01-02 10:30:01 - INFO - Task ee73a218-6292-43e3-9052-f495745aa646 validated successfully: 6 images
2025-01-02 10:30:01 - INFO - Updated task ee73a218-6292-43e3-9052-f495745aa646 status to VALIDATED
```

## Error Handling

- **MongoDB connection errors**: Process exits with error code 1
- **Individual task errors**: Logged and continue processing other tasks
- **PDF validation errors**: Task marked as FAILED with error details
- **File not found**: Task marked as FAILED

## Stopping the Process

Use `Ctrl+C` to gracefully stop the process. The script will:
- Complete current task processing
- Close MongoDB connection
- Exit cleanly

## Requirements

Install dependencies:
```bash
pip install -r requirements.txt
```

Key dependencies:
- `pymongo`: MongoDB client
- `pdf2image`: PDF to image conversion
- Other existing dependencies from your project

## Integration with Existing Workflow

This process integrates with your existing MongoDB-based document processing:

1. **Document upload** creates entries in `File_document` collection
2. **Task creation** adds entries to `Task` collection with `NOT_STARTED` status
3. **This validator** processes tasks and updates status to `VALIDATED`/`VALIDATION_FAILED`
4. **Downstream processes** can then pick up `VALIDATED` tasks for further processing 