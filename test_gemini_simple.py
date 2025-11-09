#!/usr/bin/env python3
"""
Simple Gemini API Test
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_gemini_connection():
    """Test basic Gemini API connection."""
    try:
        import google.generativeai as genai
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("❌ GEMINI_API_KEY not found in environment")
            return False
            
        print(f"🔑 API Key found: {api_key[:10]}...")
        
        # Configure Gemini
        genai.configure(api_key=api_key)
        
        # Test with a simple model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Simple test prompt
        response = model.generate_content("Hello, this is a test. Please respond with 'API connection successful!'")
        
        print("✅ Gemini API Connection Test:")
        print(f"Response: {response.text}")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False
    except Exception as e:
        print(f"❌ Gemini API Error: {e}")
        return False

def test_basic_components():
    """Test basic system components."""
    print("🧪 Testing Basic Components...")
    
    # Test environment
    api_key = os.getenv('GEMINI_API_KEY')
    print(f"✅ Environment: API Key {'found' if api_key else 'missing'}")
    
    # Test imports
    try:
        import requests
        import json
        from datetime import datetime
        print("✅ Basic imports: OK")
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Test regex patterns
    import re
    test_text = "My Aadhaar is 1234 5678 9012 and email is test@example.com"
    
    aadhaar_pattern = r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b'
    email_pattern = r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'
    
    aadhaar_found = re.findall(aadhaar_pattern, test_text)
    email_found = re.findall(email_pattern, test_text)
    
    print(f"✅ Regex test: Aadhaar={aadhaar_found}, Email={email_found}")
    
    return True

if __name__ == "__main__":
    print("🚀 H4$HCR4CK$ Simple System Test")
    print("=" * 40)
    
    # Test basic components first
    if not test_basic_components():
        print("❌ Basic component test failed")
        exit(1)
    
    # Test Gemini API
    if test_gemini_connection():
        print("\n🎉 All tests passed! System is ready.")
        print("\n📋 Next steps:")
        print("1. Initialize database: python3 -c \"from database.models import initialize_database; initialize_database()\"")
        print("2. Start Tor and Privoxy services")
        print("3. Run the crawler: bash launcher.sh")
    else:
        print("\n⚠️  Gemini API test failed, but basic components work.")
        print("You can still use the system with regex-only detection.")
        print("Check your API key and internet connection.")
