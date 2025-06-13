import os
from pathlib import Path
from process_checks import CheckProcessor

def test_check_processor():
    # Initialize the processor
    processor = CheckProcessor()
    
    # Get the test PDF path
    test_pdf = Path("test_data/sample_checks.pdf")
    
    if not test_pdf.exists():
        print(f"Please place a test PDF file at {test_pdf}")
        return
    
    # Process the PDF
    result = processor.process_pdf(str(test_pdf))
    
    if result:
        print("Test completed successfully!")
        
        # Verify the CSV file
        csv_file = Path("data/processed_checks.csv")
        if csv_file.exists():
            print(f"CSV file created at: {csv_file}")
            print("CSV contents:")
            with open(csv_file, 'r') as f:
                print(f.read())
    else:
        print("Test failed. Check the logs for more details.")

if __name__ == "__main__":
    test_check_processor() 