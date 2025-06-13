import os
import uuid
import cv2
import json
import numpy as np
import pandas as pd
from pdf2image import convert_from_path
from google.cloud import vision
from openai import OpenAI
from dotenv import load_dotenv
from pathlib import Path
from utils.logger import setup_logger
from utils.google_auth import setup_google_vision_auth
from utils.image_analyzer import analyze_check_image
from models.check import CheckDetails

# Load environment variables
load_dotenv()

# Setup logger
logger = setup_logger()

class CheckProcessor:
    def __init__(self):
        # Initialize Google Vision client with proper authentication
        try:
            self.vision_client = setup_google_vision_auth()
            logger.info("Successfully initialized Google Vision client")
        except Exception as e:
            logger.error(f"Failed to initialize Google Vision client: {str(e)}")
            raise

        # Initialize OpenAI client with API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        self.openai_client = OpenAI(api_key=api_key)
        
        self.checks_dir = Path("data/checks")
        self.csv_file = Path("data/processed_checks.csv")
        
        # Create directories if they don't exist
        self.checks_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize CSV if it doesn't exist
        if not self.csv_file.exists():
            self._initialize_csv()
            logger.info("Initialized new CSV file for check processing")

    def _initialize_csv(self):
        """Initialize CSV file with headers"""
        headers = [
            "check_id", "payee_name", "amount", "date", "check_number",
            "check_transit_number", "check_institution_number", "check_bank_account_number",
            "bank", "company_name_address", "raw_text"
        ]
        pd.DataFrame(columns=headers).to_csv(self.csv_file, index=False)

    def extract_images_from_pdf(self, pdf_path):
        """Extract images from PDF and determine front/back for each check"""
        logger.info(f"Converting PDF to images: {pdf_path}")
        images = convert_from_path(pdf_path)
        
        # Process images in pairs
        check_images = []
        for i in range(0, len(images), 2):
            # testing logic for a single image
            if i > 3:
                break
            if i + 1 < len(images):
                # Analyze both images to determine which is front/back
                first_image = images[i]
                second_image = images[i + 1]
                
                # Get text from both images in one pass
                is_first_front, first_text = analyze_check_image(first_image, self.vision_client)
                is_second_front, second_text = analyze_check_image(second_image, self.vision_client)
                
                if is_first_front:
                    check_pair = {
                        'front': first_image,
                        'back': second_image,
                        'front_text': first_text,
                        'back_text': second_text
                    }
                    logger.info(f"Check {len(check_images)+1}: First page is front")
                else:
                    check_pair = {
                        'front': second_image,
                        'back': first_image,
                        'front_text': second_text,
                        'back_text': first_text
                    }
                    logger.info(f"Check {len(check_images)+1}: Second page is front")
            else:
                # Handle unpaired page
                single_image = images[i]
                is_front, text = analyze_check_image(single_image, self.vision_client)
                check_pair = {
                    'front': single_image,
                    'back': None,
                    'front_text': text,
                    'back_text': None
                }
                if is_front:
                    logger.info(f"Check {len(check_images)+1}: Single page identified as front")
                else:
                    logger.warning(f"Check {len(check_images)+1}: Single page appears to be a back - might miss front information")
            
            check_images.append(check_pair)
        
        logger.info(f"Found {len(check_images)} checks in PDF")
        return check_images

    def clean_image(self, image):
        """Clean and enhance the check image"""
        # Convert PIL Image to OpenCV format
        opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        
        # Apply basic image processing
        gray = cv2.cvtColor(opencv_image, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray)
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        return binary

    def save_check_image(self, front_image, back_image, check_id):
        """Save both front and back images of the check"""
        check_dir = self.checks_dir / check_id
        check_dir.mkdir(exist_ok=True)
        
        # Save front image
        front_path = check_dir / "check_front.png"
        cv2.imwrite(str(front_path), front_image)
        
        # Save back image if available
        back_path = None
        if back_image is not None:
            back_path = check_dir / "check_back.png"
            cv2.imwrite(str(back_path), back_image)
        
        return front_path, back_path

    def extract_text_from_image(self, image_path):
        """Extract text from image using Google Vision API"""
        with open(image_path, "rb") as image_file:
            content = image_file.read()
        
        image = vision.Image(content=content)
        response = self.vision_client.text_detection(image=image)
        return response.text_annotations[0].description if response.text_annotations else ""

    def parse_check_details(self, front_text, back_text=None):
        """Parse check details using ChatGPT and return a validated CheckDetails object"""
        # Combine front and back text for raw_text field
        combined_text = front_text + ("\n" + back_text if back_text else "")
        
        # Clean up the text for the prompt
        front_text_cleaned = front_text.replace('\n', ' ').replace('"', '\\"')
        back_text_cleaned = back_text.replace('\n', ' ').replace('"', '\\"') if back_text else ""
        
        prompt = (
            "Extract the following details from the given text blob. Pay special attention to the MICR line format and date extraction.\n"
            "CRITICAL: Return ONLY the raw JSON object. DO NOT include any markdown formatting, code blocks, or explanation text.\n\n"
            "Text:\n"
            f"{front_text_cleaned}\n"
            f"{back_text_cleaned}\n"
            "Required details:\n"
            "- **Date Extraction (High Priority):**\n"
            "    1. First, look for date format indicators like:\n"
            "       - YYYYMMDD\n"
            "       - DDMMYYYY\n"
            "       - MMDDYYYY\n"
            "       - YYYY MM DD\n"
            "       - DD MM YYYY\n"
            "       These are usually printed on the check to indicate the expected date format.\n\n"
            "    2. Once you find the format indicator, use it to correctly interpret the actual date.\n"
            "       Example: If format is YYYYMMDD and date shows 2024-10-31, parse as October 31, 2024\n\n"
            "    3. Common locations for date format indicators:\n"
            "       - Near 'DATE' text\n"
            "       - Above or below the date field\n"
            "       - In small print near date area\n\n"
            "    4. Always convert the final date to DD/MM/YYYY format in the output\n\n"
            "- **MICR Line Parsing (Most Important):**\n"
            "    The MICR line at the bottom of the check follows this exact format:\n"
            "    ⑈[check_number]⑈ ⑆[transit_number]⑉[institution_number]⑆ [account_number]⑈\n"
            "    Example: ⑈004921⑈ ⑆06222⑉003⑆ 102⑉813⑉3⑈\n"
            "    - Check Number: Between first pair of ⑈ symbols (004921)\n"
            "    - Transit Number: Between ⑆ and ⑉ symbols (06222)\n"
            "    - Institution Number: Between ⑉ and ⑆ symbols (003)\n"
            "    - Account Number: Numbers after last ⑆, may contain ⑉ symbols (102-813-3)\n\n"
            "- **Payee Name:**\n"
            "    - Look for the actual service provider or individual name that follows 'PAY to the order of'\n"
            "    - The payee is often a service name or individual name, NOT the company details that follow\n"
            "    - Example: In 'PAY to the order of JOHN DOE SERVICES 123 COMPANY ST...', the payee is 'JOHN DOE SERVICES'\n"
            "- **Company Name and Address:**\n"
            "    - This is typically the detailed business information that follows the payee name\n"
            "    - Should include full address and contact information if available\n"
            "    - Example: '123 COMPANY ST, CITY, STATE 12345 Tel: 123-456-7890'\n"
            "- Amount:\n" 
            "    - Look for the amount of the check, include decimal places if present\n"
            "    - Example: '$1,145.29'\n"
            "- Bank:\n"
            "    - Include the complete bank name and branch information\n\n"
            "Special Instructions:\n"
            "1. MICR Line is the highest priority - ensure exact parsing of check number, transit number, institution number, and account number\n"
            "2. For dates: First find format indicator, then parse date accordingly\n"
            "3. For payee name: Look specifically after 'PAY to the order of' and before any address/company details\n"
            "4. For company details: Capture all business information including address and contact details\n"
            "5. For bank: Include complete bank name with branch details\n"
            "6. If a field is missing, return \"Not Found\" instead of guessing\n"
            "7. IMPORTANT: Do not include any line breaks in the field values. Replace them with spaces.\n\n"
            "\nReturn Format Instructions:\n"
            "1. Return ONLY the JSON object itself\n"
            "2. DO NOT wrap the response in ```json or ``` or any other formatting\n"
            "3. DO NOT include any explanation before or after the JSON\n"
            "4. The response should start with { and end with } with no other characters\n"
            "5. Use this exact format:\n"
            '{"payee_name": "", "amount": "", "date": "", "check_number": "", "check_transit_number": "", '
            '"check_institution_number": "", "check_bank_account_number": "", "bank": "", "company_name_address": ""}'
        )

        response = self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a precise check parser that returns ONLY raw JSON objects. Never use markdown formatting or code blocks. Your response must start with { and end with } with no other characters."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.0,
            max_tokens=300
        )
        
        try:
            response_text = response.choices[0].message.content.strip()
            # Remove any markdown formatting if present
            if response_text.startswith("```"):
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
            response_text = response_text.strip()
            
            # Parse the JSON response
            json_response = json.loads(response_text)
            # Add the raw text to the response
            json_response['raw_text'] = combined_text
            # Create and validate CheckDetails object
            check_details = CheckDetails(**json_response)
            return check_details
        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(f"Raw response: {response.choices[0].message.content}")
            raise
        except Exception as e:
            logger.error(f"Failed to parse check details: {str(e)}")
            raise

    def add_to_csv(self, check_id: str, check_details: CheckDetails):
        """Add processed check details to CSV file"""
        df = pd.DataFrame([{
            "check_id": check_id,
            **check_details.model_dump()  # Use model_dump() instead of dict()
        }])
        df.to_csv(self.csv_file, mode='a', header=False, index=False)

    def process_pdf(self, pdf_path):
        """Main function to process PDF containing checks"""
        try:
            # Extract images from PDF
            check_images = self.extract_images_from_pdf(pdf_path)
            logger.info(f"Found {len(check_images)} checks in PDF")

            for idx, check_pair in enumerate(check_images):
                # Generate unique ID for this check
                check_id = str(uuid.uuid4())
                logger.info(f"Processing check {idx + 1}/{len(check_images)} (ID: {check_id})")

                # Clean both front and back images
                cleaned_front = self.clean_image(check_pair['front'])
                cleaned_back = self.clean_image(check_pair['back']) if check_pair['back'] is not None else None
                
                # Save both images
                front_path, back_path = self.save_check_image(cleaned_front, cleaned_back, check_id)
                logger.info(f"Saved check images to {front_path} and {back_path}")

                # Parse check details using cached text
                check_details = self.parse_check_details(check_pair['front_text'], check_pair['back_text'])
                logger.info("Check details parsed successfully")

                # Add to CSV
                self.add_to_csv(check_id, check_details)
                logger.info(f"Added check {check_id} to CSV")

            logger.info("PDF processing completed successfully")
            return True

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Process checks from a PDF file.')
    parser.add_argument('pdf_path', help='Path to the PDF file containing checks')
    args = parser.parse_args()

    processor = CheckProcessor()
    processor.process_pdf(args.pdf_path)

if __name__ == "__main__":
    main()