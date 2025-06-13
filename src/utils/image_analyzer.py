import cv2
import numpy as np
from PIL import Image
from google.cloud import vision
from typing import Tuple, Optional

def analyze_check_image(image, vision_client) -> Tuple[bool, Optional[str]]:
    """
    Analyze image to determine if it's front of check and return extracted text.
    Uses text_detection for basic text extraction.
    
    Args:
        image: PIL Image object
        vision_client: Authenticated Google Vision client
    
    Returns:
        Tuple[bool, Optional[str]]: (is_front, extracted_text)
    """
    # Convert PIL image to bytes
    img_byte_arr = image_to_bytes(image)
    
    # Get text annotations using text_detection
    vision_image = vision.Image(content=img_byte_arr)
    response = vision_client.text_detection(image=vision_image)
    
    if not response.text_annotations:
        return False, None
    
    # Get the full text from the first annotation
    full_text = response.text_annotations[0].description
    lower_text = full_text.lower()
    
    # Keywords typically found on check fronts
    front_indicators = [
        'pay to', 'pay', 'dollars', 'signature', 'date',
        'memo', 'void after', 'order of', '$', 'amount'
    ]
    
    # Keywords typically found on check backs
    back_indicators = [
        'endorse', 'endorsement', 'deposit', 'back of check',
        'do not write', 'below this line'
    ]
    
    front_score = sum(1 for word in front_indicators if word in lower_text)
    back_score = sum(1 for word in back_indicators if word in lower_text)
    
    return front_score > back_score, full_text

def get_text_with_positions(image, vision_client) -> list:
    """
    Get text with their positions in reading order.
    
    Args:
        image: PIL Image object
        vision_client: Authenticated Google Vision client
    
    Returns:
        list: List of dicts containing text and their bounding boxes
    """
    img_byte_arr = image_to_bytes(image)
    vision_image = vision.Image(content=img_byte_arr)
    response = vision_client.document_text_detection(image=vision_image)
    
    text_blocks = []
    if response.full_text_annotation:
        for page in response.full_text_annotation.pages:
            for block in page.blocks:
                # Get bounding box vertices
                vertices = [(vertex.x, vertex.y) for vertex in block.bounding_box.vertices]
                
                # Calculate top-left corner (for sorting)
                top_left_x = min(v[0] for v in vertices)
                top_left_y = min(v[1] for v in vertices)
                
                # Extract text from block
                block_text = ''
                for paragraph in block.paragraphs:
                    for word in paragraph.words:
                        word_text = ''.join([symbol.text for symbol in word.symbols])
                        block_text += word_text + ' '
                
                text_blocks.append({
                    'text': block_text.strip(),
                    'position': (top_left_x, top_left_y),
                    'vertices': vertices
                })
    
    # Sort blocks by y-coordinate first (top to bottom), then x-coordinate (left to right)
    return sorted(text_blocks, key=lambda b: (b['position'][1], b['position'][0]))

def image_to_bytes(pil_image) -> bytes:
    """Convert PIL Image to bytes"""
    import io
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    return img_byte_arr.getvalue() 