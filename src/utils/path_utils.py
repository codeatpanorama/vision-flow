from pathlib import Path

def extract_document_id_from_path(pdf_path):
    """
    Extract document ID from PDF path.
    
    Expected format: repository/bank_checks/{documentId}/documentId.pdf
    
    Args:
        pdf_path (str): Path to the PDF file
        
    Returns:
        str: Document ID or None if not found
    """
    try:
        # Convert to Path object for cross-platform compatibility
        path = Path(pdf_path)
        
        # Get the parent directory name (which should be the document ID)
        document_id = path.parent.name
        
        # Validate that it looks like a document ID (not empty, not 'bank_checks')
        if document_id and document_id != 'bank_checks':
            return document_id
        
        return None
        
    except Exception:
        return None
