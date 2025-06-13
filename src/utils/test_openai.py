from openai import OpenAI
from dotenv import load_dotenv
import os

def test_openai_auth():
    """
    Test OpenAI authentication using the API key from .env file
    """
    # Load environment variables
    load_dotenv()
    
    # Check if API key is set
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ Error: OPENAI_API_KEY not found in .env file")
        return False
    
    if api_key == "your_openai_api_key":
        print("❌ Error: OPENAI_API_KEY is still set to default value")
        return False
    
    try:
        # Initialize OpenAI client
        client = OpenAI()
        
        # Make a simple API call to test authentication
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Hello, this is a test message."}
            ],
            max_tokens=10
        )
        
        print("✅ OpenAI authentication successful!")
        print("Model responded with:", response.choices[0].message.content)
        return True
        
    except Exception as e:
        print(f"❌ Error testing OpenAI authentication: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing OpenAI Authentication...")
    test_openai_auth() 