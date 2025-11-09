#!/usr/bin/env python3
"""
Comprehensive Test Suite for H4$HCR4CK$ AI-Powered Dark Web Leak Detection System
Tests all AI components including Gemini integration, OCR, NER, and database functions.

Author: H4$HCR4CK$ Team
"""

import os
import sys
import json
import tempfile
import logging
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_environment_setup():
    """Test environment variables and configuration."""
    print("🔧 Testing Environment Setup...")
    
    required_env_vars = [
        'GEMINI_API_KEY',
        'DASHBOARD_USERNAME', 
        'DASHBOARD_PASSWORD'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print("Please create a .env file based on .env.example")
        return False
    
    print("✅ Environment setup validated")
    return True

def test_ai_utils():
    """Test AI utilities and Gemini integration."""
    print("🧠 Testing AI Utils and Gemini Integration...")
    
    try:
        from ai_utils import GeminiAIProcessor, detect_and_classify_leaks, validate_gemini_setup
        
        # Test Gemini setup validation
        if not validate_gemini_setup():
            print("❌ Gemini API validation failed")
            return False
        
        print("✅ Gemini API connection validated")
        
        # Test AI processor initialization
        processor = GeminiAIProcessor()
        print("✅ GeminiAIProcessor initialized successfully")
        
        # Test local regex detection
        test_text = """
        My Aadhaar number is 1234 5678 9012 and PAN card is ABCDE1234F.
        Contact me at john.doe@example.com or call 9876543210.
        Bank account: 1234567890123456
        """
        
        local_results = processor.run_local_regex_detection(test_text)
        print(f"✅ Local regex detection: Found {len(local_results)} entity types")
        
        # Test full AI detection workflow
        full_results = detect_and_classify_leaks(test_text, processor)
        print("✅ Full AI detection workflow completed")
        
        # Test Gemini leak detection
        gemini_result = processor.detect_leaks_with_gemini(test_text[:1000])  # Limit text length
        print(f"✅ Gemini leak detection: Confidence {gemini_result.get('confidence_score', 0)}%")
        
        # Test OCR text processing
        ocr_result = processor.process_ocr_text("Sample OCR text with potential PII")
        print("✅ OCR text processing completed")
        
        return True
        
    except Exception as e:
        print(f"❌ AI Utils test failed: {str(e)}")
        return False

def test_ner_utils():
    """Test enhanced NER utilities."""
    print("🔍 Testing Enhanced NER Utils...")
    
    try:
        from crawler.ner_utils import extract_entities, validate_aadhaar, validate_pan, validate_ifsc
        
        test_text = """
        Contact Details:
        Aadhaar: 1234 5678 9012
        PAN: ABCDE1234F
        Email: test@example.com
        Phone: +91 9876543210
        IFSC: SBIN0001234
        Bank Account: 1234567890123456
        IMEI: 123456789012345
        """
        
        entities = extract_entities(test_text)
        print(f"✅ NER extraction: Found {len(entities)} entity types")
        
        for entity_type, values in entities.items():
            print(f"  📌 {entity_type}: {len(values)} matches")
        
        # Test validation functions
        print("✅ Aadhaar validation:", validate_aadhaar("123456789012"))
        print("✅ PAN validation:", validate_pan("ABCDE1234F"))
        print("✅ IFSC validation:", validate_ifsc("SBIN0001234"))
        
        return True
        
    except Exception as e:
        print(f"❌ NER Utils test failed: {str(e)}")
        return False

def test_ocr_processor():
    """Test OCR document processor."""
    print("📄 Testing OCR Document Processor...")
    
    try:
        from ocr_parser import OCRDocumentProcessor, is_ocr_available, validate_file_for_ocr
        
        if not is_ocr_available():
            print("⚠️  OCR dependencies not available, skipping OCR tests")
            return True
        
        # Create a simple test image (would need actual image for full test)
        print("✅ OCR dependencies available")
        
        # Test file validation
        is_valid, message = validate_file_for_ocr("/nonexistent/file.jpg")
        print(f"✅ File validation test: {message}")
        
        # Initialize processor
        processor = OCRDocumentProcessor()
        print("✅ OCR processor initialized")
        
        processor.cleanup()
        return True
        
    except ImportError:
        print("⚠️  OCR dependencies not installed, skipping OCR tests")
        return True
    except Exception as e:
        print(f"❌ OCR Processor test failed: {str(e)}")
        return False

def test_database_functions():
    """Test database operations and AI workflow integration."""
    print("🗄️  Testing Database Functions...")
    
    try:
        from database.models import (
            initialize_database, fetch_all_data_ai, get_leak_statistics,
            export_leaks_json, search_by_identifier_db
        )
        
        # Initialize database
        initialize_database()
        print("✅ Database initialized")
        
        # Test statistics
        stats = get_leak_statistics()
        print(f"✅ Statistics retrieved: {stats['total_records']} total records")
        
        # Test search functionality
        search_results = search_by_identifier_db("test", limit=5)
        print(f"✅ Search by identifier: {len(search_results)} results")
        
        # Test JSON export
        json_data = export_leaks_json(limit=5)
        print(f"✅ JSON export: {len(json_data)} records exported")
        
        return True
        
    except Exception as e:
        print(f"❌ Database functions test failed: {str(e)}")
        return False

def test_crawler_integration():
    """Test crawler AI integration."""
    print("🕷️  Testing Crawler AI Integration...")
    
    try:
        # Import crawler modules
        sys.path.append(os.path.join(os.path.dirname(__file__), 'crawler'))
        from decimal_crawler import DecimalCrawlerSpider
        
        print("✅ Crawler modules imported successfully")
        
        # Test spider initialization (without actually crawling)
        spider = DecimalCrawlerSpider()
        print(f"✅ Spider initialized with AI enabled: {spider.ai_enabled}")
        
        return True
        
    except Exception as e:
        print(f"❌ Crawler integration test failed: {str(e)}")
        return False

def test_dashboard_api():
    """Test dashboard API endpoints."""
    print("🌐 Testing Dashboard API...")
    
    try:
        from dashboard.decimal_dashboard import app
        
        with app.test_client() as client:
            # Test login page
            response = client.get('/')
            print(f"✅ Login page accessible: {response.status_code}")
            
            # Test API endpoints (would need authentication for full test)
            print("✅ Dashboard app initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Dashboard API test failed: {str(e)}")
        return False

def test_json_output_format():
    """Test JSON output structure and format."""
    print("📊 Testing JSON Output Format...")
    
    try:
        from database.models import export_leaks_json
        
        # Test with no filters
        json_data = export_leaks_json(limit=3)
        
        if json_data:
            sample_leak = json_data[0]
            required_fields = ['id', 'url', 'title', 'discovered_at', 'ai_analysis']
            
            for field in required_fields:
                if field not in sample_leak:
                    print(f"❌ Missing required field: {field}")
                    return False
            
            print("✅ JSON structure validation passed")
        else:
            print("⚠️  No data available for JSON format testing")
        
        return True
        
    except Exception as e:
        print(f"❌ JSON output test failed: {str(e)}")
        return False

def create_test_report(test_results: Dict[str, bool]) -> str:
    """Generate a comprehensive test report."""
    report = f"""
    
=== H4$HCR4CK$ AI-Powered Leak Detection System Test Report ===
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Test Results:
{'='*60}
"""
    
    total_tests = len(test_results)
    passed_tests = sum(test_results.values())
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        report += f"{test_name:<40} {status}\n"
    
    report += f"\n{'='*60}\n"
    report += f"Total Tests: {total_tests}\n"
    report += f"Passed: {passed_tests}\n"
    report += f"Failed: {total_tests - passed_tests}\n"
    report += f"Success Rate: {(passed_tests/total_tests)*100:.1f}%\n"
    
    if passed_tests == total_tests:
        report += "\n🎉 ALL TESTS PASSED! System is ready for deployment.\n"
    else:
        report += f"\n⚠️  {total_tests - passed_tests} tests failed. Please review and fix issues.\n"
    
    report += "\nNext Steps:\n"
    report += "1. Ensure Gemini API key is configured in .env file\n"
    report += "2. Install OCR dependencies if needed: sudo apt-get install tesseract-ocr\n"
    report += "3. Install Python dependencies: pip install google-generativeai pytesseract pillow pdf2image\n"
    report += "4. Start the system using: bash launcher.sh\n"
    
    return report

def main():
    """Main test execution function."""
    print("🚀 Starting H4$HCR4CK$ AI System Validation...")
    print("=" * 60)
    
    # Define tests to run
    tests = {
        "Environment Setup": test_environment_setup,
        "AI Utils & Gemini": test_ai_utils,
        "NER Utils": test_ner_utils,
        "OCR Processor": test_ocr_processor,
        "Database Functions": test_database_functions,
        "Crawler Integration": test_crawler_integration,
        "Dashboard API": test_dashboard_api,
        "JSON Output Format": test_json_output_format,
    }
    
    # Run tests
    results = {}
    for test_name, test_func in tests.items():
        try:
            print(f"\n{test_name}")
            print("-" * 40)
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results[test_name] = False
    
    # Generate and display report
    report = create_test_report(results)
    print(report)
    
    # Save report to file
    report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"\n📋 Test report saved to: {report_file}")
    
    # Return overall success
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
