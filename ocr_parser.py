"""
OCR and Document Parser Module
Uses Tesseract OCR to extract text from images/PDFs and processes them with Gemini AI.

Author: H4$HCR4CK$ Team
Requirements: tesseract-ocr, pytesseract, pdf2image, pillow
"""

import os
import logging
import tempfile
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path
import json
import base64

try:
    import pytesseract
    from PIL import Image
    import pdf2image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logging.warning("OCR dependencies not available. Install: pip install pytesseract pillow pdf2image")

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("Requests not available. Install: pip install requests")

from ai_utils import GeminiAIProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRDocumentProcessor:
    """OCR document processor with Gemini AI integration."""
    
    def __init__(self, gemini_processor: GeminiAIProcessor = None):
        """Initialize OCR processor with Gemini AI."""
        if not TESSERACT_AVAILABLE:
            raise ImportError("OCR dependencies missing. Install: tesseract-ocr, pytesseract, pdf2image, pillow")
        
        self.gemini_processor = gemini_processor or GeminiAIProcessor()
        self.temp_dir = tempfile.mkdtemp(prefix="ocr_processing_")
        
        # Configure Tesseract (adjust path if needed)
        self.configure_tesseract()
        
    def configure_tesseract(self):
        """Configure Tesseract OCR settings."""
        # Try to find Tesseract executable
        possible_paths = [
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract',
            '/opt/homebrew/bin/tesseract',  # macOS with Homebrew
            'tesseract'  # System PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or path == 'tesseract':
                try:
                    pytesseract.pytesseract.tesseract_cmd = path
                    # Test if it works
                    pytesseract.get_tesseract_version()
                    logger.info(f"Tesseract configured at: {path}")
                    break
                except Exception:
                    continue
        else:
            logger.warning("Tesseract not found in common paths. Ensure it's installed and in PATH.")
    
    def extract_text_from_image(self, image_path: str, language: str = 'eng') -> Dict[str, Any]:
        """
        Extract text from image using OCR.
        
        Args:
            image_path: Path to image file
            language: Language code for OCR (default: eng)
        
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Open image
            image = Image.open(image_path)
            
            # Configure OCR settings for better accuracy
            custom_config = r'--oem 3 --psm 6'
            
            # Extract text
            raw_text = pytesseract.image_to_string(image, lang=language, config=custom_config)
            
            # Get confidence scores
            data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            result = {
                'raw_text': raw_text,
                'cleaned_text': raw_text.strip(),
                'confidence': avg_confidence,
                'word_count': len(raw_text.split()),
                'character_count': len(raw_text),
                'language': language,
                'image_path': image_path,
                'processing_successful': True
            }
            
            logger.info(f"OCR extraction successful. Confidence: {avg_confidence:.2f}%, Words: {result['word_count']}")
            return result
            
        except Exception as e:
            logger.error(f"OCR extraction failed for {image_path}: {str(e)}")
            return {
                'raw_text': '',
                'cleaned_text': '',
                'confidence': 0,
                'word_count': 0,
                'character_count': 0,
                'language': language,
                'image_path': image_path,
                'processing_successful': False,
                'error': str(e)
            }
    
    def extract_text_from_pdf(self, pdf_path: str, language: str = 'eng', 
                            max_pages: int = 10) -> Dict[str, Any]:
        """
        Extract text from PDF by converting to images first.
        
        Args:
            pdf_path: Path to PDF file
            language: Language code for OCR
            max_pages: Maximum number of pages to process
        
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            # Convert PDF to images
            images = pdf2image.convert_from_path(pdf_path, first_page=1, last_page=max_pages)
            
            all_text = []
            all_confidences = []
            total_words = 0
            
            for i, image in enumerate(images):
                # Save temporary image
                temp_image_path = os.path.join(self.temp_dir, f"page_{i+1}.png")
                image.save(temp_image_path)
                
                # Extract text from page
                page_result = self.extract_text_from_image(temp_image_path, language)
                
                if page_result['processing_successful']:
                    all_text.append(f"[Page {i+1}]\\n{page_result['cleaned_text']}")
                    all_confidences.append(page_result['confidence'])
                    total_words += page_result['word_count']
                
                # Clean up temp image
                try:
                    os.remove(temp_image_path)
                except:
                    pass
            
            combined_text = "\\n\\n".join(all_text)
            avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
            
            result = {
                'raw_text': combined_text,
                'cleaned_text': combined_text.strip(),
                'confidence': avg_confidence,
                'word_count': total_words,
                'character_count': len(combined_text),
                'pages_processed': len(images),
                'language': language,
                'pdf_path': pdf_path,
                'processing_successful': True
            }
            
            logger.info(f"PDF OCR successful. Pages: {len(images)}, Confidence: {avg_confidence:.2f}%")
            return result
            
        except Exception as e:
            logger.error(f"PDF OCR failed for {pdf_path}: {str(e)}")
            return {
                'raw_text': '',
                'cleaned_text': '',
                'confidence': 0,
                'word_count': 0,
                'character_count': 0,
                'pages_processed': 0,
                'language': language,
                'pdf_path': pdf_path,
                'processing_successful': False,
                'error': str(e)
            }
    
    def download_and_process_image(self, image_url: str, language: str = 'eng') -> Dict[str, Any]:
        """
        Download image from URL and process with OCR.
        
        Args:
            image_url: URL of the image
            language: Language code for OCR
        
        Returns:
            Dictionary with extracted text and metadata
        """
        if not REQUESTS_AVAILABLE:
            return {
                'error': 'Requests library not available',
                'processing_successful': False
            }
        
        try:
            # Download image
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            # Save to temporary file
            temp_image_path = os.path.join(self.temp_dir, f"downloaded_image.{image_url.split('.')[-1]}")
            
            with open(temp_image_path, 'wb') as f:
                f.write(response.content)
            
            # Process with OCR
            result = self.extract_text_from_image(temp_image_path, language)
            result['source_url'] = image_url
            
            # Clean up
            try:
                os.remove(temp_image_path)
            except:
                pass
            
            return result
            
        except Exception as e:
            logger.error(f"Download and OCR failed for {image_url}: {str(e)}")
            return {
                'raw_text': '',
                'cleaned_text': '',
                'confidence': 0,
                'source_url': image_url,
                'processing_successful': False,
                'error': str(e)
            }
    
    def process_with_gemini_ai(self, ocr_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process OCR text with Gemini AI for cleaning and entity extraction.
        
        Args:
            ocr_result: Result from OCR processing
        
        Returns:
            Enhanced result with AI processing
        """
        if not ocr_result['processing_successful'] or not ocr_result['cleaned_text']:
            return ocr_result
        
        try:
            # Process with Gemini AI
            ai_result = self.gemini_processor.process_ocr_text(ocr_result['cleaned_text'])
            
            # Combine OCR and AI results
            enhanced_result = ocr_result.copy()
            enhanced_result.update({
                'ai_processed': True,
                'ai_cleaned_text': ai_result['cleaned_text'],
                'ai_extracted_entities': ai_result['extracted_entities'],
                'ai_document_type': ai_result['document_type'],
                'ai_confidence': ai_result['confidence'],
                'ai_notes': ai_result['notes'],
                'processing_timestamp': None  # Will be set by caller
            })
            
            logger.info(f"AI processing completed. Document type: {ai_result['document_type']}")
            return enhanced_result
            
        except Exception as e:
            logger.error(f"Gemini AI processing failed: {str(e)}")
            ocr_result['ai_processed'] = False
            ocr_result['ai_error'] = str(e)
            return ocr_result
    
    def process_document_complete(self, file_path: str, language: str = 'eng') -> Dict[str, Any]:
        """
        Complete document processing pipeline: OCR + AI processing.
        
        Args:
            file_path: Path to document (image or PDF)
            language: Language code for OCR
        
        Returns:
            Complete processing result
        """
        file_extension = Path(file_path).suffix.lower()
        
        # Determine processing method
        if file_extension == '.pdf':
            ocr_result = self.extract_text_from_pdf(file_path, language)
        elif file_extension in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            ocr_result = self.extract_text_from_image(file_path, language)
        else:
            return {
                'error': f'Unsupported file format: {file_extension}',
                'processing_successful': False,
                'file_path': file_path
            }
        
        # Process with AI if OCR was successful
        if ocr_result['processing_successful']:
            final_result = self.process_with_gemini_ai(ocr_result)
            final_result['processing_timestamp'] = None  # Set by caller if needed
            return final_result
        else:
            return ocr_result
    
    def batch_process_documents(self, file_paths: List[str], language: str = 'eng') -> List[Dict[str, Any]]:
        """
        Process multiple documents in batch.
        
        Args:
            file_paths: List of file paths to process
            language: Language code for OCR
        
        Returns:
            List of processing results
        """
        results = []
        
        for file_path in file_paths:
            logger.info(f"Processing document: {file_path}")
            result = self.process_document_complete(file_path, language)
            results.append(result)
        
        logger.info(f"Batch processing completed. Processed {len(results)} documents.")
        return results
    
    def extract_pii_from_documents(self, file_paths: List[str], language: str = 'eng') -> Dict[str, Any]:
        """
        Extract PII specifically from documents using OCR + AI.
        
        Args:
            file_paths: List of document paths
            language: OCR language
        
        Returns:
            Comprehensive PII extraction results
        """
        all_pii = {
            'documents_processed': 0,
            'documents_with_pii': 0,
            'total_entities_found': 0,
            'entities_by_type': {},
            'documents': [],
            'summary': {}
        }
        
        for file_path in file_paths:
            doc_result = self.process_document_complete(file_path, language)
            
            if doc_result['processing_successful'] and doc_result.get('ai_processed'):
                all_pii['documents_processed'] += 1
                
                entities = doc_result.get('ai_extracted_entities', {})
                if any(entities.values()):
                    all_pii['documents_with_pii'] += 1
                    
                    # Count entities by type
                    for entity_type, entity_list in entities.items():
                        if entity_list:
                            all_pii['entities_by_type'][entity_type] = all_pii['entities_by_type'].get(entity_type, 0) + len(entity_list)
                            all_pii['total_entities_found'] += len(entity_list)
                
                all_pii['documents'].append({
                    'file_path': file_path,
                    'document_type': doc_result.get('ai_document_type', 'Unknown'),
                    'entities': entities,
                    'confidence': doc_result.get('ai_confidence', 0),
                    'processing_successful': True
                })
            else:
                all_pii['documents'].append({
                    'file_path': file_path,
                    'processing_successful': False,
                    'error': doc_result.get('error', 'Processing failed')
                })
        
        # Generate summary
        if all_pii['documents_processed'] > 0:
            all_pii['summary'] = {
                'success_rate': (all_pii['documents_with_pii'] / all_pii['documents_processed']) * 100,
                'avg_entities_per_doc': all_pii['total_entities_found'] / all_pii['documents_processed'],
                'most_common_entity_type': max(all_pii['entities_by_type'].items(), key=lambda x: x[1])[0] if all_pii['entities_by_type'] else None
            }
        
        return all_pii
    
    def cleanup(self):
        """Clean up temporary files."""
        try:
            import shutil
            shutil.rmtree(self.temp_dir)
            logger.info("OCR processor cleanup completed.")
        except Exception as e:
            logger.warning(f"Cleanup failed: {str(e)}")


# Utility functions
def is_ocr_available() -> bool:
    """Check if OCR capabilities are available."""
    return TESSERACT_AVAILABLE

def get_supported_formats() -> List[str]:
    """Get list of supported file formats."""
    return ['.pdf', '.png', '.jpg', '.jpeg', '.tiff', '.bmp']

def validate_file_for_ocr(file_path: str) -> Tuple[bool, str]:
    """
    Validate if file can be processed with OCR.
    
    Returns:
        Tuple of (is_valid, message)
    """
    if not os.path.exists(file_path):
        return False, "File does not exist"
    
    file_extension = Path(file_path).suffix.lower()
    if file_extension not in get_supported_formats():
        return False, f"Unsupported format: {file_extension}"
    
    try:
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit
            return False, "File too large (>50MB)"
        
        if file_size == 0:
            return False, "File is empty"
        
    except Exception as e:
        return False, f"Cannot access file: {str(e)}"
    
    return True, "File is valid for OCR processing"


if __name__ == "__main__":
    # Test OCR processor
    print("🔍 Testing OCR Document Processor...")
    
    if not is_ocr_available():
        print("❌ OCR dependencies not available!")
        print("Install with: sudo apt-get install tesseract-ocr && pip install pytesseract pillow pdf2image")
        exit(1)
    
    try:
        processor = OCRDocumentProcessor()
        print("✅ OCR processor initialized successfully!")
        
        # Test with a sample image (create a simple test)
        test_files = []
        for ext in ['.png', '.jpg', '.pdf']:
            test_file = f"/tmp/test_ocr{ext}"
            if os.path.exists(test_file):
                test_files.append(test_file)
        
        if test_files:
            print(f"📄 Processing {len(test_files)} test files...")
            results = processor.batch_process_documents(test_files)
            print(f"✅ Processed {len(results)} documents successfully!")
        else:
            print("ℹ️  No test files found. OCR processor is ready for use.")
        
        processor.cleanup()
        
    except Exception as e:
        print(f"❌ OCR processor test failed: {str(e)}")
        print("Make sure Gemini API is configured and OCR dependencies are installed.")
