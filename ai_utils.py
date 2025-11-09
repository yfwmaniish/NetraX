"""
AI Utilities Module for Dark Web Leak Detection
Uses Google Gemini API for intelligent leak detection, classification, and analysis.

Author: H4$HCR4CK$ Team
"""

import os
import re
import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiAIProcessor:
    """Main class for handling all AI-driven leak detection operations using Gemini."""
    
    def __init__(self, api_key: str = None):
        """Initialize Gemini AI processor with API key."""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Enhanced regex patterns for local PII detection
        self.local_patterns = {
            "Aadhaar": [
                r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',  # Standard format
                r'\b\d{12}\b',  # Without spaces/hyphens
                r'(?i)(?:aadhaar|aadhar)[\s\-]?(?:number|no|id)?[\s\-]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            ],
            "PAN": [
                r'\b[A-Z]{5}\d{4}[A-Z]\b',  # Standard PAN format
                r'(?i)(?:pan|permanent[\s]+account)[\s\-]?(?:number|no|card)?[\s\-]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
            ],
            "Phone": [
                r'\b(?:\+91[\s\-]?)?[6-9]\d{9}\b',  # Indian mobile numbers
                r'(?i)(?:phone|mobile|contact)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\+?91[\s\-]?[6-9]\d{9})',
                r'\b(?:0\d{2,4}[\s\-]?\d{6,8})\b',  # Landline numbers
            ],
            "Email": [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
                r'(?i)(?:email|e-mail|mail)[\s\-]*:?[\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            ],
            "IFSC": [
                r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
                r'(?i)(?:ifsc|bank[\s]+code)[\s\-]*:?[\s]*([A-Z]{4}0[A-Z0-9]{6})',
            ],
            "Credit_Card": [
                r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
                r'(?i)(?:card|cc)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            ],
            "Bank_Account": [
                r'\b\d{9,18}\b',  # Generic bank account pattern
                r'(?i)(?:account|a/c)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\d{9,18})',
            ],
            "Telecom_Data": [
                r'(?i)(?:imei|imsi|msisdn)[\s\-]*:?[\s]*(\d{10,18})',
                r'(?i)(?:sim|subscriber)[\s\-]?(?:id|number)?[\s\-]*:?[\s]*(\d{10,20})',
            ],
            "Government_ID": [
                r'(?i)(?:passport|driving[\s]+license|voter[\s]+id)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*([A-Z0-9]{6,12})',
                r'(?i)(?:ration[\s]+card|election[\s]+id)[\s\-]*:?[\s]*([A-Z0-9]{8,15})',
            ]
        }
    
    def run_local_regex_detection(self, text: str) -> Dict[str, List[str]]:
        """
        Run local regex rules for initial PII detection.
        Returns dict with category as key and list of matches as values.
        """
        detected_entities = {}
        
        for category, patterns in self.local_patterns.items():
            matches = set()  # Use set to avoid duplicates
            
            for pattern in patterns:
                found_matches = re.findall(pattern, text, re.IGNORECASE)
                if isinstance(found_matches, list):
                    matches.update(found_matches)
                else:
                    matches.add(found_matches)
            
            if matches:
                detected_entities[category] = list(matches)
        
        logger.info(f"Local regex detected: {len(detected_entities)} categories")
        return detected_entities
    
    def detect_leaks_with_gemini(self, text_snippet: str, max_length: int = 4000) -> Dict[str, Any]:
        """
        Send suspicious text snippets to Gemini for context-aware PII detection.
        """
        # Truncate text if too long
        if len(text_snippet) > max_length:
            text_snippet = text_snippet[:max_length] + "..."
        
        prompt = f"""
        Analyze the following text for potential data leaks and PII (Personally Identifiable Information).
        Focus on detecting:
        - Aadhaar numbers (Indian national ID)
        - PAN cards (Indian tax ID)
        - Phone numbers (especially Indian numbers)
        - Email addresses
        - Banking/Financial information
        - Telecom data (IMEI, SIM details)
        - KYC documents references
        - Credit card information
        - Government IDs (passport, driving license, voter ID)
        
        Text to analyze:
        \"\"\"
        {text_snippet}
        \"\"\"
        
        Please respond in JSON format with:
        {{
            "leak_detected": true/false,
            "confidence_score": 0-100,
            "detected_entities": {{
                "Aadhaar": ["list of aadhaar numbers"],
                "PAN": ["list of PAN numbers"],
                "Phone": ["list of phone numbers"],
                "Email": ["list of emails"],
                "Banking": ["list of banking info"],
                "Telecom": ["list of telecom data"],
                "Government_ID": ["list of govt IDs"],
                "Other_PII": ["other sensitive data"]
            }},
            "context": "brief description of the leak context",
            "severity": "LOW/MEDIUM/HIGH/CRITICAL"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"Gemini leak detection completed with confidence: {result.get('confidence_score', 0)}")
            return result
        except Exception as e:
            logger.error(f"Gemini leak detection failed: {str(e)}")
            return {
                "leak_detected": False,
                "confidence_score": 0,
                "detected_entities": {},
                "context": "Error during analysis",
                "severity": "LOW"
            }
    
    def classify_leak_data(self, leak_records: List[Dict]) -> Dict[str, Any]:
        """
        Send extracted records to Gemini for classification.
        Categories: ["Aadhaar", "PAN", "Telecom", "Banking/Financial", "General PII"]
        """
        
        # Prepare data summary for classification
        data_summary = []
        for record in leak_records[:10]:  # Limit to first 10 records for prompt
            summary = {
                "entities": record.get('detected_entities', {}),
                "context": record.get('context', ''),
                "url": record.get('url', '')
            }
            data_summary.append(summary)
        
        prompt = f"""
        Classify the following data leak records into appropriate categories.
        Available categories: ["Aadhaar", "PAN", "Telecom", "Banking/Financial", "General PII", "Government Documents", "Healthcare", "Educational"]
        
        Records to classify:
        {json.dumps(data_summary, indent=2)}
        
        Please respond in JSON format:
        {{
            "primary_classification": "main category",
            "secondary_classifications": ["additional categories"],
            "records_by_category": {{
                "Aadhaar": number_of_records,
                "PAN": number_of_records,
                "Telecom": number_of_records,
                "Banking/Financial": number_of_records,
                "General PII": number_of_records,
                "Government Documents": number_of_records,
                "Healthcare": number_of_records,
                "Educational": number_of_records
            }},
            "overall_severity": "LOW/MEDIUM/HIGH/CRITICAL",
            "risk_assessment": "brief risk analysis",
            "affected_individuals_estimate": estimated_number
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"Gemini classification completed: {result.get('primary_classification', 'Unknown')}")
            return result
        except Exception as e:
            logger.error(f"Gemini classification failed: {str(e)}")
            return {
                "primary_classification": "General PII",
                "secondary_classifications": [],
                "records_by_category": {"General PII": len(leak_records)},
                "overall_severity": "MEDIUM",
                "risk_assessment": "Classification error occurred",
                "affected_individuals_estimate": len(leak_records)
            }
    
    def process_ocr_text(self, ocr_text: str) -> Dict[str, Any]:
        """
        Clean and extract entities from OCR text using Gemini.
        """
        prompt = f"""
        The following text was extracted from an image/PDF using OCR and may contain errors.
        Please clean the text and extract any PII (Personally Identifiable Information).
        
        OCR Text:
        \"\"\"
        {ocr_text}
        \"\"\"
        
        Please respond in JSON format:
        {{
            "cleaned_text": "corrected and cleaned text",
            "extracted_entities": {{
                "names": ["list of person names"],
                "addresses": ["list of addresses"],
                "phone_numbers": ["list of phone numbers"],
                "email_addresses": ["list of emails"],
                "id_numbers": ["list of ID numbers"],
                "financial_info": ["banking/financial details"]
            }},
            "document_type": "type of document (passport, license, etc.)",
            "confidence": 0-100,
            "notes": "any additional observations"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"OCR processing completed for document type: {result.get('document_type', 'Unknown')}")
            return result
        except Exception as e:
            logger.error(f"OCR processing failed: {str(e)}")
            return {
                "cleaned_text": ocr_text,
                "extracted_entities": {},
                "document_type": "Unknown",
                "confidence": 0,
                "notes": "Processing error occurred"
            }
    
    def fuzzy_match_identifier(self, identifier: str, dataset_description: str) -> Dict[str, Any]:
        """
        Use Gemini to check if a dataset matches an identifier with fuzzy matching.
        """
        prompt = f"""
        Check if the following dataset description contains information related to the given identifier.
        Consider fuzzy matching, partial matches, and related information.
        
        Identifier to search: "{identifier}"
        Dataset description: "{dataset_description}"
        
        Please respond in JSON format:
        {{
            "match_found": true/false,
            "confidence": 0-100,
            "match_type": "EXACT/PARTIAL/FUZZY/RELATED/NONE",
            "matched_elements": ["list of matching elements found"],
            "explanation": "brief explanation of the match",
            "recommended_action": "what should be done with this match"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"Fuzzy matching completed: {result.get('match_type', 'NONE')} match")
            return result
        except Exception as e:
            logger.error(f"Fuzzy matching failed: {str(e)}")
            return {
                "match_found": False,
                "confidence": 0,
                "match_type": "NONE",
                "matched_elements": [],
                "explanation": "Error during matching",
                "recommended_action": "Manual review required"
            }
    
    def generate_incident_summary(self, leak_data: Dict) -> Dict[str, Any]:
        """
        Generate a human-readable incident summary from JSON leak results.
        """
        prompt = f"""
        Create a concise, professional incident summary report based on the following data leak information:
        
        Leak Data:
        {json.dumps(leak_data, indent=2)}
        
        Please respond in JSON format:
        {{
            "incident_title": "brief descriptive title",
            "executive_summary": "2-3 sentence overview",
            "affected_data_types": ["list of data types compromised"],
            "estimated_records": number,
            "severity_level": "LOW/MEDIUM/HIGH/CRITICAL",
            "key_findings": ["bullet points of main findings"],
            "recommendations": ["security recommendations"],
            "timeline": "when this likely occurred or was discovered",
            "impact_assessment": "potential impact description"
        }}
        """
        
        try:
            response = self.model.generate_content(prompt)
            result = json.loads(response.text)
            logger.info(f"Incident summary generated: {result.get('severity_level', 'Unknown')} severity")
            return result
        except Exception as e:
            logger.error(f"Summary generation failed: {str(e)}")
            return {
                "incident_title": "Data Leak Detected",
                "executive_summary": "A data leak has been identified requiring further investigation.",
                "affected_data_types": ["Unknown"],
                "estimated_records": 0,
                "severity_level": "MEDIUM",
                "key_findings": ["Analysis error occurred"],
                "recommendations": ["Manual review required"],
                "timeline": datetime.now().strftime("%Y-%m-%d"),
                "impact_assessment": "Impact assessment pending"
            }


# Helper functions for integration with existing system
def detect_and_classify_leaks(text: str, ai_processor: GeminiAIProcessor = None) -> Dict[str, Any]:
    """
    Main function to detect and classify leaks using the complete AI workflow.
    """
    if not ai_processor:
        ai_processor = GeminiAIProcessor()
    
    # Step 1: Local regex detection
    local_results = ai_processor.run_local_regex_detection(text)
    
    # Step 2: If local detection finds something suspicious, use Gemini
    if local_results:
        gemini_results = ai_processor.detect_leaks_with_gemini(text)
        
        # Combine results
        combined_results = {
            "local_detection": local_results,
            "ai_detection": gemini_results,
            "processed_at": datetime.now().isoformat(),
            "detection_method": "hybrid"
        }
        
        return combined_results
    else:
        return {
            "local_detection": {},
            "ai_detection": {"leak_detected": False, "confidence_score": 0},
            "processed_at": datetime.now().isoformat(),
            "detection_method": "local_only"
        }


def search_by_identifier(identifier: str, leak_index: List[Dict], ai_processor: GeminiAIProcessor = None) -> List[Dict]:
    """
    Search leak index by identifier with AI fuzzy matching.
    """
    if not ai_processor:
        ai_processor = GeminiAIProcessor()
    
    matches = []
    
    # First check local exact matches
    for record in leak_index:
        record_text = f"{record.get('title', '')} {record.get('entities', '')} {record.get('url', '')}"
        if identifier.lower() in record_text.lower():
            record['match_type'] = 'local_exact'
            matches.append(record)
    
    # If no exact matches and we have ambiguous results, use Gemini
    if len(matches) == 0 or len(matches) > 10:
        for record in leak_index[:20]:  # Limit to first 20 for AI processing
            dataset_desc = f"Title: {record.get('title', '')} | Entities: {record.get('entities', '')} | URL: {record.get('url', '')}"
            fuzzy_result = ai_processor.fuzzy_match_identifier(identifier, dataset_desc)
            
            if fuzzy_result['match_found'] and fuzzy_result['confidence'] > 70:
                record['ai_match'] = fuzzy_result
                record['match_type'] = 'ai_fuzzy'
                matches.append(record)
    
    return matches


# Configuration and validation
def validate_gemini_setup() -> bool:
    """Validate that Gemini API is properly configured."""
    try:
        processor = GeminiAIProcessor()
        test_result = processor.detect_leaks_with_gemini("Test message for API validation")
        return test_result is not None
    except Exception as e:
        logger.error(f"Gemini setup validation failed: {str(e)}")
        return False


if __name__ == "__main__":
    # Test the AI processor
    print("🧠 Testing AI Processor...")
    
    if validate_gemini_setup():
        print("✅ Gemini API setup validated successfully!")
        
        # Test with sample data
        processor = GeminiAIProcessor()
        
        # Test local regex
        test_text = "My Aadhaar is 1234 5678 9012 and PAN is ABCDE1234F. Contact: 9876543210"
        local_results = processor.run_local_regex_detection(test_text)
        print(f"📍 Local detection results: {local_results}")
        
    else:
        print("❌ Gemini API setup validation failed!")
        print("Make sure to set GEMINI_API_KEY environment variable")
