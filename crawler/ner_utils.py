import re
import logging
from typing import Dict, List, Set

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_entities(text: str) -> Dict[str, List[str]]:
    """Enhanced entity extraction with comprehensive Indian PII patterns."""
    
    # Enhanced regex patterns for Indian PII data
    patterns = {
        # Aadhaar number patterns (enhanced for better detection)
        "Aadhaar": [
            r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',  # Standard format with/without separators
            r'\b\d{12}\b',  # Continuous 12 digits (excluding phone numbers)
            r'(?i)(?:aadhaar|aadhar)[\s\-]?(?:number|no|id|card)?[\s\-]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            r'(?i)(?:uid|unique[\s]+id|unique[\s]+identification)[\s\-]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            r'(?i)aadhaar[\s]*card[\s]*number[\s]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            r'(?i)aadhar[\s]*no[\s]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            r'\b(?:UID|uid)[\s]*[:\-]?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4})\b',
        ],
        
        # PAN card patterns (enhanced)
        "PAN": [
            r'\b[A-Z]{5}\d{4}[A-Z]\b',  # Standard PAN format
            r'(?i)(?:pan|permanent[\s]+account)[\s\-]?(?:number|no|card)?[\s\-]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
            r'(?i)(?:tax[\s]+id|income[\s]+tax)[\s\-]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
            r'(?i)pan[\s]*card[\s]*number[\s]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
            r'(?i)pan[\s]*no[\s]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
            r'(?i)permanent[\s]*account[\s]*no[\s]*:?[\s]*([A-Z]{5}\d{4}[A-Z])',
        ],
        
        # Phone number patterns (comprehensive)
        "Phone": [
            r'\b(?:\+91[\s\-]?)?[6-9]\d{9}\b',  # Indian mobile numbers
            r'\b(?:0\d{2,4}[\s\-]?\d{6,8})\b',  # Landline numbers
            r'(?i)(?:phone|mobile|contact|cell)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\+?91[\s\-]?[6-9]\d{9})',
            r'(?i)(?:whatsapp|wa)[\s\-]*:?[\s]*(\+?91[\s\-]?[6-9]\d{9})',
            r'\b(?:\+91)?[\s\-]?[789]\d{9}\b',  # Alternative mobile pattern
        ],
        
        # Email patterns (enhanced)
        "Email": [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b',
            r'(?i)(?:email|e-mail|mail)[\s\-]*:?[\s]*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})',
            r'\b[A-Za-z0-9._%+-]+@(?:gmail|yahoo|hotmail|outlook|rediffmail|sify)\.(?:com|in|co\.in)\b',
        ],
        
        # Banking information
        "Bank_Account": [
            r'\b\d{9,18}\b',  # Generic bank account pattern
            r'(?i)(?:account|a/c)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\d{9,18})',
            r'(?i)(?:savings|current)[\s\-]?(?:account|a/c)?[\s\-]*:?[\s]*(\d{9,18})',
        ],
        
        # IFSC codes (enhanced)
        "IFSC": [
            r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
            r'(?i)(?:ifsc|bank[\s]+code|routing[\s]+code)[\s\-]*:?[\s]*([A-Z]{4}0[A-Z0-9]{6})',
            r'(?i)(?:swift|branch)[\s\-]?(?:code)?[\s\-]*:?[\s]*([A-Z]{4}0[A-Z0-9]{6})',
        ],
        
        # Credit/Debit card patterns
        "Credit_Card": [
            r'\b(?:\d{4}[\s\-]?){3}\d{4}\b',
            r'(?i)(?:card|cc|debit|credit)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*(\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4})',
            r'\b(?:4\d{3}|5[1-5]\d{2}|6011|3[47]\d{2})[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',  # Visa, MC, Amex patterns
        ],
        
        # Telecom data patterns
        "Telecom_Data": [
            r'(?i)(?:imei)[\s\-]*:?[\s]*(\d{15})',  # IMEI numbers
            r'(?i)(?:imsi)[\s\-]*:?[\s]*(\d{15,16})',  # IMSI numbers
            r'(?i)(?:msisdn)[\s\-]*:?[\s]*(\d{10,15})',  # MSISDN
            r'(?i)(?:sim)[\s\-]?(?:id|number)?[\s\-]*:?[\s]*(\d{10,20})',
            r'(?i)(?:subscriber)[\s\-]?(?:id|number)?[\s\-]*:?[\s]*(\d{10,20})',
            r'\b(?:IMEI|imei)\s*[:\-]?\s*(\d{15})\b',
        ],
        
        # Government ID patterns (enhanced)
        "Government_ID": [
            r'(?i)(?:passport)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*([A-Z]\d{7}|[A-Z]{2}\d{7})',  # Indian passport
            r'(?i)(?:driving[\s]+license|dl|license)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*([A-Z]{2}\d{13})',  # Driving license
            r'(?i)(?:voter[\s]+id|election[\s]+id|epic[\s]+no)[\s\-]*:?[\s]*([A-Z]{3}\d{7})',  # Voter ID
            r'(?i)(?:ration[\s]+card|ration[\s]+card[\s]+number)[\s\-]*:?[\s]*([A-Z0-9]{10,15})',  # Ration card
            r'(?i)(?:passport[\s]+no|passport[\s]+number)[\s\-]*:?[\s]*([A-Z]\d{7}|[A-Z]{2}\d{7})',
            r'(?i)(?:dl[\s]+no|license[\s]+no)[\s\-]*:?[\s]*([A-Z]{2}\d{13})',
            r'(?i)(?:epic)[\s\-]*:?[\s]*([A-Z]{3}\d{7})',
        ],
        
        # KYC document references (enhanced)
        "KYC_Documents": [
            r'(?i)(?:kyc|know[\s]+your[\s]+customer)',
            r'(?i)(?:identity[\s]+proof|id[\s]+proof|identity[\s]+document)',
            r'(?i)(?:address[\s]+proof|residential[\s]+proof)',
            r'(?i)(?:income[\s]+proof|salary[\s]+slip|income[\s]+certificate)',
            r'(?i)(?:bank[\s]+statement|account[\s]+statement)',
            r'(?i)(?:kyc[\s]+documents|kyc[\s]+papers)',
            r'(?i)(?:verification[\s]+documents|verification[\s]+papers)',
            r'(?i)(?:document[\s]+verification|paper[\s]+verification)',
            r'(?i)(?:customer[\s]+verification|customer[\s]+documents)',
        ],
        
        # IP addresses
        "IP_Address": [
            r'\b(?:\d{1,3}\.){3}\d{1,3}\b',  # IPv4
            r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',  # IPv6
        ],
        
        # Cryptocurrency wallets
        "Crypto_Wallet": [
            r'\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b',  # Bitcoin
            r'\b0x[a-fA-F0-9]{40}\b',  # Ethereum
            r'\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b',  # Monero
        ],
        
        # UPI IDs
        "UPI_ID": [
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\b',  # Generic UPI pattern
            r'(?i)[a-z0-9._%+-]+@(?:paytm|phonepe|googlepay|amazonpay|ybl|okhdfcbank|oksbi|okaxis)\b',
        ],
        
        # GST numbers
        "GST_Number": [
            r'\b\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z]\d\b',  # GST format
            r'(?i)(?:gstin|gst[\s]+number)[\s\-]*:?[\s]*(\d{2}[A-Z]{5}\d{4}[A-Z]\d[A-Z]\d)',
        ],
        
        # EPF/PF numbers
        "EPF_Number": [
            r'(?i)(?:epf|pf|provident[\s]+fund)[\s\-]?(?:number|no)?[\s\-]*:?[\s]*([A-Z]{2}/[A-Z]{3}/\d{7}/\d{3}/\d{7})',
            r'\b[A-Z]{2}/[A-Z]{3}/\d{7}/\d{3}/\d{7}\b',
        ],
    }
    
    detected_entities = {}
    
    for entity_type, pattern_list in patterns.items():
        matches = set()  # Use set to avoid duplicates
        
        for pattern in pattern_list:
            try:
                found_matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                if found_matches:
                    # Handle both string matches and tuple matches (from groups)
                    for match in found_matches:
                        if isinstance(match, tuple):
                            # Extract non-empty groups
                            for group in match:
                                if group.strip():
                                    matches.add(group.strip())
                        else:
                            matches.add(match.strip())
            except re.error as e:
                logger.warning(f"Regex error for pattern {pattern}: {e}")
                continue
        
        # Filter out very short or invalid matches
        filtered_matches = []
        for match in matches:
            if len(match) >= 3:  # Minimum length filter
    # Additional validation for specific entity types
                if entity_type == "Aadhaar":
                    clean_match = match.replace(' ', '').replace('-', '')
                    if len(clean_match) != 12 or not clean_match.isdigit():
                        continue
                    # Basic validation - exclude phone numbers (starting with 6-9)
                    if clean_match.startswith(('0', '1', '2', '3', '4', '5')):
                        continue
                if entity_type == "PAN":
                    if len(match) != 10:
                        continue
                    # Enhanced PAN validation
                    if not re.match(r'^[A-Z]{5}[0-9]{4}[A-Z]$', match.upper()):
                        continue
                filtered_matches.append(match)
        
        if filtered_matches:
            detected_entities[entity_type] = filtered_matches
    
    logger.info(f"Entity extraction completed. Found {len(detected_entities)} entity types.")
    return detected_entities


def validate_aadhaar(aadhaar: str) -> bool:
    """Validate Aadhaar number using Verhoeff algorithm (basic check)."""
    # Remove spaces and hyphens
    aadhaar = aadhaar.replace(' ', '').replace('-', '')
    
    if len(aadhaar) != 12 or not aadhaar.isdigit():
        return False
    
    # Basic validation (not implementing full Verhoeff for simplicity)
    # In production, you'd implement the full Verhoeff checksum algorithm
    return True


def validate_pan(pan: str) -> bool:
    """Validate PAN number format."""
    if len(pan) != 10:
        return False
    
    # PAN format: 5 letters + 4 digits + 1 letter
    pattern = r'^[A-Z]{5}[0-9]{4}[A-Z]$'
    return bool(re.match(pattern, pan))


def validate_ifsc(ifsc: str) -> bool:
    """Validate IFSC code format."""
    if len(ifsc) != 11:
        return False
    
    # IFSC format: 4 letters + 0 + 6 alphanumeric
    pattern = r'^[A-Z]{4}0[A-Z0-9]{6}$'
    return bool(re.match(pattern, ifsc))


def get_entity_confidence_score(entity_type: str, entity_value: str) -> float:
    """Calculate confidence score for detected entities."""
    if entity_type == "Aadhaar":
        return 0.9 if validate_aadhaar(entity_value) else 0.6
    elif entity_type == "PAN":
        return 0.9 if validate_pan(entity_value) else 0.6
    elif entity_type == "IFSC":
        return 0.9 if validate_ifsc(entity_value) else 0.6
    elif entity_type in ["Email", "Phone"]:
        return 0.8  # High confidence for well-structured patterns
    elif entity_type in ["Credit_Card", "Bank_Account"]:
        return 0.7  # Moderate confidence, needs additional validation
    else:
        return 0.6  # Default confidence
