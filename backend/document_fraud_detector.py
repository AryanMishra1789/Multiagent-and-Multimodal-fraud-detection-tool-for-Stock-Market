import os
import re
import tempfile
import base64
from datetime import datetime
import cv2
import numpy as np
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from llm_utils import gemini_llm  # Changed from relative to absolute import

# Configure Tesseract path for OCR
# Try to automatically detect the Tesseract path on Windows
import platform
if platform.system() == 'Windows':
    import os.path
    # Common installation paths for Tesseract on Windows
    possible_paths = [
        r'tesseract',  # If it's in the PATH
        r'C:\Program Files\Tesseract-OCR\tesseract.exe',
        r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        r'C:\Users\Hp\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'  # Common user installation path
    ]
    
    # Use the first path that exists
    for path in possible_paths:
        if path == 'tesseract' or os.path.exists(path):
            pytesseract.pytesseract.tesseract_cmd = path
            break
else:
    # On Linux/Mac, it's usually in the PATH
    pytesseract.pytesseract.tesseract_cmd = r'tesseract'

class DocumentFraudDetector:
    def __init__(self):
        # Common fraud indicators in financial documents
        self.fraud_keywords = [
            "guaranteed returns", "risk-free", "100% safe", "double your money",
            "secret investment", "exclusive opportunity", "limited time", 
            "inside information", "huge profits", "secret formula", "get rich quick",
            "hidden assets", "offshore account", "tax-free guaranteed", "unreported",
            "bypass", "loophole", "backdoor", "unreported income", "cash only",
            "no questions", "no paperwork", "avoid taxes", "no risk", "untraceable"
        ]
        
        # Regular expressions for detecting suspicious patterns
        self.patterns = {
            "tampered_dates": r"(?<!\d)(?:19|20)\d{2}(?:[.,/-])(?:0?[1-9]|1[012])(?:[.,/-])(?:0?[1-9]|[12][0-9]|3[01])(?!\d)",
            "large_amounts": r"(?:Rs\.?|₹|INR)\s*\d{7,}(?:\.\d{1,2})?",
            "unusual_symbols": r"[©®™℗℠№†‡§¶⁂]",
            "blurred_areas": None  # Detected computationally
        }
        
        # Known official document headers (examples for demo)
        self.known_headers = [
            "SECURITIES AND EXCHANGE BOARD OF INDIA",
            "SEBI",
            "RESERVE BANK OF INDIA",
            "RBI",
            "MINISTRY OF FINANCE",
            "BOMBAY STOCK EXCHANGE",
            "NATIONAL STOCK EXCHANGE",
            "BSE LIMITED",
            "NSE INDIA",
            "INCOME TAX DEPARTMENT"
        ]
        
        # Known official document footers
        self.known_footers = [
            "www.sebi.gov.in",
            "www.rbi.org.in",
            "www.bseindia.com",
            "www.nseindia.com",
            "www.incometaxindia.gov.in"
        ]
    
    def extract_text_from_image(self, image_path):
        """Extract text from an image using OCR"""
        try:
            # Check if Tesseract is installed and configured
            try:
                tesseract_version = pytesseract.get_tesseract_version()
                print(f"Using Tesseract version: {tesseract_version}")
            except Exception as te:
                print(f"Warning: Tesseract OCR not properly configured: {str(te)}")
                return "Tesseract OCR not properly configured. Please check installation."
            
            # Open the image
            img = cv2.imread(image_path)
            if img is None:
                return "Could not open image file or file format not supported"
                
            # Preprocessing for better OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
            
            # Detect blurry areas (could indicate tampering)
            self.blurry_regions = self._detect_blurry_regions(img)
            
            # Extract text
            text = pytesseract.image_to_string(gray)
            
            # If no text was extracted, try different preprocessing
            if not text.strip():
                # Try with adaptive thresholding
                adaptive_threshold = cv2.adaptiveThreshold(
                    gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
                )
                text = pytesseract.image_to_string(adaptive_threshold)
                
            return text if text.strip() else "No text could be extracted from the image"
        except Exception as e:
            print(f"Error in OCR processing: {str(e)}")
            return f"Error in OCR: {str(e)}"
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from a PDF document"""
        try:
            doc = fitz.open(pdf_path)
            text = ""
            for page in doc:
                text += page.get_text()
            
            # Also check for images within PDF
            images = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)
                
                for img_index, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Save image to a temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp:
                        temp.write(image_bytes)
                        temp_filename = temp.name
                    
                    # Extract text from the image
                    img_text = self.extract_text_from_image(temp_filename)
                    text += f"\n[IMAGE TEXT: {img_text}]\n"
                    
                    # Clean up
                    os.unlink(temp_filename)
            
            return text
        except Exception as e:
            return f"Error extracting text from PDF: {str(e)}"
    
    def _detect_blurry_regions(self, img):
        """Detect blurry regions in an image that might indicate tampering"""
        blurry_regions = []
        
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Calculate Laplacian variance (measure of image focus)
        lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # Check for local blurriness by splitting the image into a grid
        height, width = gray.shape
        grid_size = 50  # Size of each grid cell
        
        for y in range(0, height, grid_size):
            for x in range(0, width, grid_size):
                # Get region of interest
                roi = gray[y:min(y+grid_size, height), x:min(x+grid_size, width)]
                if roi.size == 0:
                    continue
                
                # Calculate local variance
                local_lap_var = cv2.Laplacian(roi, cv2.CV_64F).var()
                
                # If significantly lower than average, mark as suspicious
                if local_lap_var < 0.5 * lap_var:
                    blurry_regions.append({
                        'x': x,
                        'y': y,
                        'width': min(grid_size, width-x),
                        'height': min(grid_size, height-y)
                    })
        
        return blurry_regions
    
    def detect_tampering(self, text, image_path=None):
        """Detect potential tampering in the document text"""
        tampering_indicators = []
        
        # Check for multiple different date formats
        date_formats = set()
        date_matches = re.finditer(self.patterns["tampered_dates"], text)
        for match in date_matches:
            date_formats.add(match.group())
        
        if len(date_formats) > 3:  # If too many different date formats
            tampering_indicators.append({
                "type": "inconsistent_date_formats",
                "description": "Multiple inconsistent date formats detected",
                "confidence": 0.7,
                "matches": list(date_formats)[:5]  # Limited examples
            })
        
        # Check for unusual symbols in financial sections
        symbol_matches = re.finditer(self.patterns["unusual_symbols"], text)
        unusual_symbols = set(match.group() for match in symbol_matches)
        if unusual_symbols:
            tampering_indicators.append({
                "type": "unusual_symbols",
                "description": "Unusual symbols detected that may indicate tampering",
                "confidence": 0.6,
                "matches": list(unusual_symbols)
            })
        
        # Check for blurry regions (only if image was analyzed)
        if hasattr(self, 'blurry_regions') and self.blurry_regions:
            tampering_indicators.append({
                "type": "blurred_areas",
                "description": "Blurred areas detected that may indicate tampering",
                "confidence": 0.8,
                "count": len(self.blurry_regions)
            })
        
        # Check for inappropriate editing artifacts
        if "PHOTOSHOP" in text.upper() or "EDITED WITH" in text.upper() or "CREATED BY" in text.upper():
            tampering_indicators.append({
                "type": "editing_artifacts",
                "description": "Document contains editing software artifacts",
                "confidence": 0.9
            })
        
        return tampering_indicators
    
    def detect_fraudulent_content(self, text):
        """Detect potentially fraudulent content in the document"""
        fraud_indicators = []
        
        # Check for suspicious financial terms
        for keyword in self.fraud_keywords:
            if re.search(r'\b' + re.escape(keyword) + r'\b', text.lower()):
                fraud_indicators.append({
                    "type": "suspicious_term",
                    "term": keyword,
                    "description": f"Document contains suspicious term: {keyword}",
                    "confidence": 0.7
                })
        
        # Check for unusually large monetary amounts
        amount_matches = re.finditer(self.patterns["large_amounts"], text)
        large_amounts = [match.group() for match in amount_matches]
        if large_amounts:
            fraud_indicators.append({
                "type": "large_amounts",
                "description": "Unusually large monetary amounts detected",
                "confidence": 0.6,
                "amounts": large_amounts[:5]  # Limited examples
            })
        
        # Check for inconsistencies in headers and footers
        has_official_header = any(header.lower() in text.lower() for header in self.known_headers)
        has_official_footer = any(footer.lower() in text.lower() for footer in self.known_footers)
        
        if has_official_header and not has_official_footer:
            fraud_indicators.append({
                "type": "inconsistent_official_markings",
                "description": "Document has official header but missing corresponding footer",
                "confidence": 0.7
            })
        
        # Use LLM to analyze the document for suspicious content
        try:
            prompt = (
                "Analyze this document text for signs of financial fraud or misrepresentation. "
                "Look for: suspicious claims, unrealistic returns, misleading statements, "
                "impersonation of officials, or inconsistent information. "
                "Respond with a JSON containing: "
                "{'is_suspicious': boolean, 'suspicious_claims': [list of suspicious statements], "
                "'fraud_likelihood': score from 0-1, 'reasoning': brief explanation}\n\n"
                f"Document text:\n{text[:4000]}"  # Limit text length
            )
            
            response = gemini_llm(prompt)
            
            # Process the response
            import json
            try:
                # Clean response to extract just the JSON
                if response.strip().startswith('```'):
                    response = response.strip().lstrip('```').rstrip('`').strip()
                    if response.startswith('json'):
                        response = response[4:].strip()
                        
                llm_analysis = json.loads(response)
                
                if llm_analysis.get("is_suspicious", False):
                    fraud_indicators.append({
                        "type": "llm_analysis",
                        "description": "AI analysis detected potential fraud",
                        "confidence": llm_analysis.get("fraud_likelihood", 0.5),
                        "reasoning": llm_analysis.get("reasoning", ""),
                        "suspicious_claims": llm_analysis.get("suspicious_claims", [])
                    })
            except json.JSONDecodeError:
                fraud_indicators.append({
                    "type": "llm_analysis",
                    "description": "AI analysis detected potential issues",
                    "confidence": 0.5,
                    "reasoning": response[:200]  # Truncate long response
                })
                
        except Exception as e:
            fraud_indicators.append({
                "type": "analysis_error",
                "description": f"Error during advanced analysis: {str(e)}",
                "confidence": 0.3
            })
        
        return fraud_indicators
    
    def verify_document(self, file_path, file_type=None):
        """Main method to verify a document for fraud"""
        start_time = datetime.now()
        
        # Determine file type if not specified
        if not file_type:
            if file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
                file_type = "image"
            elif file_path.lower().endswith('.pdf'):
                file_type = "pdf"
            else:
                return {
                    "status": "error",
                    "message": "Unsupported file type. Please upload a PDF or image file.",
                    "timestamp": datetime.now().isoformat()
                }
        
        # Extract text based on file type
        if file_type == "image":
            text = self.extract_text_from_image(file_path)
        elif file_type == "pdf":
            text = self.extract_text_from_pdf(file_path)
        else:
            return {
                "status": "error",
                "message": "Unsupported file type. Please upload a PDF or image file.",
                "timestamp": datetime.now().isoformat()
            }
        
        # Analyze for tampering
        tampering_indicators = self.detect_tampering(text)
        
        # Analyze for fraudulent content
        fraud_indicators = self.detect_fraudulent_content(text)
        
        # Overall assessment
        is_suspicious = (len(tampering_indicators) > 0 or len(fraud_indicators) > 0)
        
        # Calculate risk score
        risk_score = 0
        for indicator in tampering_indicators:
            risk_score += indicator.get("confidence", 0.5) * 50
        for indicator in fraud_indicators:
            risk_score += indicator.get("confidence", 0.5) * 50
        
        # Cap risk score at 100
        risk_score = min(100, risk_score)
        
        # Determine verification status
        if risk_score > 70:
            verification_status = "HIGH_RISK"
        elif risk_score > 40:
            verification_status = "SUSPICIOUS"
        elif risk_score > 10:
            verification_status = "NEEDS_REVIEW"
        else:
            verification_status = "LIKELY_GENUINE"
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        
        # Generate balanced reason summary
        reason_parts = []
        
        # Count different types of issues
        fraud_terms_count = len([i for i in fraud_indicators if i["type"] == "suspicious_term"])
        has_ai_analysis = any(i["type"] == "llm_analysis" for i in fraud_indicators)
        has_blurred_areas = any(i["type"] == "blurred_areas" for i in tampering_indicators)
        has_large_amounts = any(i["type"] == "large_amounts" for i in fraud_indicators)
        has_unusual_symbols = any(i["type"] == "unusual_symbols" for i in tampering_indicators)
        
        # Add specific details for key indicators
        if fraud_terms_count > 0:
            # Get top 2-3 most concerning terms
            suspicious_terms = [i.get('term', '') for i in fraud_indicators if i["type"] == "suspicious_term"][:3]
            if fraud_terms_count <= 3:
                reason_parts.append(f"Contains suspicious terms: {', '.join(suspicious_terms)}")
            else:
                reason_parts.append(f"Contains {fraud_terms_count} suspicious terms including: {', '.join(suspicious_terms[:2])}")
        
        if has_blurred_areas:
            blurred_count = next((i.get('count', 0) for i in tampering_indicators if i["type"] == "blurred_areas"), 0)
            if blurred_count > 50:
                reason_parts.append(f"Extensive image tampering detected ({blurred_count} blurred regions)")
            elif blurred_count > 10:
                reason_parts.append(f"Multiple blurred regions detected ({blurred_count} areas)")
            else:
                reason_parts.append("Blurred areas suggesting potential tampering")
        
        if has_large_amounts:
            amounts = next((i.get('amounts', []) for i in fraud_indicators if i["type"] == "large_amounts"), [])
            if amounts:
                reason_parts.append(f"Unusually large amounts mentioned: {amounts[0]}")
        
        if has_ai_analysis:
            # Get key AI insights
            for indicator in fraud_indicators:
                if indicator["type"] == "llm_analysis":
                    ai_reasoning = indicator.get('reasoning', '')
                    suspicious_claims = indicator.get('suspicious_claims', [])
                    
                    if suspicious_claims:
                        claims_text = ', '.join(suspicious_claims[:2])
                        reason_parts.append(f"AI flagged suspicious claims: {claims_text}")
                    elif "unrealistic" in ai_reasoning.lower():
                        reason_parts.append("AI detected unrealistic financial promises")
                    elif "illegal" in ai_reasoning.lower() or "tax" in ai_reasoning.lower():
                        reason_parts.append("AI detected potentially illegal financial activities")
                    elif "scam" in ai_reasoning.lower():
                        reason_parts.append("AI analysis indicates scam characteristics")
                    break
        
        # Construct final balanced reason (3-4 lines max)
        if reason_parts:
            if len(reason_parts) <= 2:
                reason = ". ".join(reason_parts)
            else:
                # Take top 2 most important and summarize rest
                main_reasons = ". ".join(reason_parts[:2])
                additional_count = len(reason_parts) - 2
                reason = f"{main_reasons}. {additional_count} additional fraud indicators detected."
        elif is_suspicious:
            reason = "Document flagged as suspicious based on pattern analysis"
        else:
            reason = "Document appears legitimate with no significant fraud indicators detected"
        
        # Add message based on verification status
        if verification_status == "HIGH_RISK":
            message = "Document shows strong indicators of fraud or tampering"
        elif verification_status == "SUSPICIOUS":
            message = "Document contains suspicious elements requiring further review"
        elif verification_status == "NEEDS_REVIEW":
            message = "Document has minor concerns but may be legitimate"
        else:
            message = "Document analysis completed successfully"
        
        result = {
            "status": "completed",
            "verification_status": verification_status,
            "risk_score": risk_score,
            "is_suspicious": is_suspicious,
            "message": message,
            "reason": reason,
            "tampering_indicators": tampering_indicators,
            "fraud_indicators": fraud_indicators,
            "extracted_text_sample": text[:500] + "..." if len(text) > 500 else text,
            "processing_time": processing_time * 1000,  # Convert to milliseconds for consistency
            "timestamp": end_time.isoformat()
        }
        
        return result

# Convenience function for API endpoint
def verify_document(file_path, file_type=None):
    try:
        detector = DocumentFraudDetector()
        return detector.verify_document(file_path, file_type)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in document verification: {str(e)}\n{error_details}")
        return {
            "status": "error",
            "verification_status": "ERROR",
            "risk_score": 0,
            "is_suspicious": None,
            "message": f"Error processing document: {str(e)}",
            "error_details": str(e),
            "timestamp": datetime.now().isoformat()
        }

# For testing
if __name__ == "__main__":
    detector = DocumentFraudDetector()
    
    # Test with a sample file
    sample_file = "path/to/sample/document.pdf"
    if os.path.exists(sample_file):
        result = detector.verify_document(sample_file)
        print(result)
    else:
        print("Sample file not found")
