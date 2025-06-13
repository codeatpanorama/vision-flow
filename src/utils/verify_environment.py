import sys
from importlib.metadata import version, PackageNotFoundError
import importlib
from pathlib import Path

def check_package(package_name):
    """Check if a package is installed and get its version"""
    try:
        pkg_version = version(package_name)
        print(f"✅ {package_name:<20} version: {pkg_version}")
        return True
    except PackageNotFoundError:
        print(f"❌ {package_name:<20} NOT FOUND")
        return False

def test_package_functionality():
    """Test core functionality of main packages"""
    tests = []
    
    # Test OpenCV
    try:
        import cv2
        import numpy as np
        # Create a small test image
        test_image = np.zeros((100, 100, 3), dtype=np.uint8)
        # Try basic OpenCV operation
        gray = cv2.cvtColor(test_image, cv2.COLOR_BGR2GRAY)
        tests.append(("OpenCV Image Processing", True))
    except Exception as e:
        tests.append(("OpenCV Image Processing", False))
    
    # Test PDF2Image imports
    try:
        import pdf2image
        tests.append(("PDF2Image Import", True))
    except Exception as e:
        tests.append(("PDF2Image Import", False))
    
    # Test Pillow
    try:
        from PIL import Image
        tests.append(("Pillow Import", True))
    except Exception as e:
        tests.append(("Pillow Import", False))
    
    # Test NumPy
    try:
        import numpy as np
        arr = np.array([1, 2, 3])
        tests.append(("NumPy Array Creation", True))
    except Exception as e:
        tests.append(("NumPy Array Creation", False))
    
    # Test Pandas
    try:
        import pandas as pd
        df = pd.DataFrame({'test': [1, 2, 3]})
        tests.append(("Pandas DataFrame Creation", True))
    except Exception as e:
        tests.append(("Pandas DataFrame Creation", False))
    
    # Test Google Cloud Vision
    try:
        from google.cloud import vision
        tests.append(("Google Cloud Vision Import", True))
    except Exception as e:
        tests.append(("Google Cloud Vision Import", False))
    
    # Test OpenAI
    try:
        from openai import OpenAI
        tests.append(("OpenAI Import", True))
    except Exception as e:
        tests.append(("OpenAI Import", False))
    
    # Test python-dotenv
    try:
        from dotenv import load_dotenv
        tests.append(("Python-dotenv Import", True))
    except Exception as e:
        tests.append(("Python-dotenv Import", False))
    
    return tests

def main():
    print("\n=== Checking Required Packages ===\n")
    
    # Check core packages
    required_packages = [
        'opencv-python',
        'numpy',
        'pandas',
        'Pillow',
        'pdf2image',
        'google-cloud-vision',
        'openai',
        'python-dotenv'
    ]
    
    all_packages_found = all(check_package(pkg) for pkg in required_packages)
    
    print("\n=== Testing Package Functionality ===\n")
    
    # Run functionality tests
    test_results = test_package_functionality()
    for test_name, success in test_results:
        if success:
            print(f"✅ {test_name:<30} OK")
        else:
            print(f"❌ {test_name:<30} FAILED")
    
    print("\n=== Python Environment Information ===\n")
    print(f"Python version: {sys.version}")
    print(f"Python location: {sys.executable}")
    
    if all_packages_found:
        print("\n✅ All required packages are installed!")
    else:
        print("\n❌ Some packages are missing. Please check the output above.")
    
    all_tests_passed = all(success for _, success in test_results)
    if all_tests_passed:
        print("✅ All functionality tests passed!")
    else:
        print("❌ Some functionality tests failed. Please check the output above.")

if __name__ == "__main__":
    main() 