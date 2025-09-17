"""
PDF Processor Module - Handles PDF extraction functionality
"""

import os
import PyPDF2
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import tempfile
import logging
import shutil
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def is_poppler_installed():
    """Check if Poppler is installed and accessible."""
    if os.name == 'nt':  # Windows
        return shutil.which('pdftoppm') is not None or shutil.which('pdftoppm.exe') is not None
    else:  # Linux, macOS
        return shutil.which('pdftoppm') is not None

class PDFProcessor:
    def __init__(self, pdf_path=None):
        """Initialize the PDF processor with an optional path to a PDF."""
        self.pdf_path = pdf_path
        self.text_content = {}
        self.images = []
        self.metadata = {}
        self.total_pages = 0
        self.poppler_available = is_poppler_installed()
        
        if not self.poppler_available:
            logger.warning("Poppler is not installed or not in PATH. Image extraction will be limited.")
            logger.info("Install Poppler: https://github.com/oschwartz10612/poppler-windows/releases/ (Windows)")
            logger.info("Or use: brew install poppler (macOS) or apt-get install poppler-utils (Linux)")
        
    def load_pdf(self, pdf_path):
        """Load a PDF from the given path."""
        try:
            self.pdf_path = pdf_path
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                self.total_pages = len(reader.pages)
                self.metadata = reader.metadata if reader.metadata else {}
            logger.info(f"Loaded PDF: {pdf_path} with {self.total_pages} pages")
            return True
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            return False
    
    def extract_text(self):
        """Extract text from all pages of the PDF using pdfplumber."""
        if not self.pdf_path:
            logger.error("No PDF loaded")
            return False
        
        try:
            self.text_content = {}
            with pdfplumber.open(self.pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    self.text_content[i+1] = page_text
            logger.info(f"Extracted text from {len(self.text_content)} pages")
            return True
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            return False
    
    def extract_images(self):
        """Extract images from the PDF using pdf2image."""
        if not self.pdf_path:
            logger.error("No PDF loaded")
            return False
        
        if not self.poppler_available:
            logger.warning("Image extraction requires Poppler. Please install it and add to PATH.")
            self.images = []  # Empty list since we can't extract
            return False
        
        try:
            # Convert PDF pages to images
            images = convert_from_path(self.pdf_path)
            self.images = images
            logger.info(f"Extracted {len(images)} image(s) from PDF")
            return True
        except Exception as e:
            logger.error(f"Error extracting images: {str(e)}")
            self.images = []  # Reset on failure
            return False
    
    def ocr_image(self, image):
        """Perform OCR on a single image to extract text."""
        try:
            text = pytesseract.image_to_string(image)
            return text
        except Exception as e:
            logger.error(f"OCR error: {str(e)}")
            return ""
    
    def ocr_pdf(self):
        """Run OCR on all pages of the PDF and update text content."""
        if not self.pdf_path:
            logger.error("No PDF loaded")
            return False
            
        try:
            # Extract images if not already done
            if not self.images:
                self.extract_images()
                
            # Perform OCR on each image
            for i, image in enumerate(self.images):
                # If the page already has text, check if OCR provides more content
                page_num = i + 1
                existing_text = self.text_content.get(page_num, "")
                
                # If existing text is short or empty, use OCR
                if len(existing_text) < 100:
                    ocr_text = self.ocr_image(image)
                    
                    # If OCR found more text, use it
                    if len(ocr_text) > len(existing_text):
                        self.text_content[page_num] = ocr_text
                        
            logger.info("Completed OCR on PDF pages")
            return True
        except Exception as e:
            logger.error(f"Error during OCR processing: {str(e)}")
            return False
            
    def get_text_by_page(self, page_num):
        """Get the text content of a specific page."""
        return self.text_content.get(page_num, "")
    
    def get_all_text(self):
        """Get the text content of the entire PDF as a single string."""
        if not self.text_content:
            return ""
        
        all_text = ""
        for page in range(1, self.total_pages + 1):
            all_text += self.text_content.get(page, "") + "\n\n"
        return all_text
    
    def save_image(self, page_num, output_path):
        """Save a specific page as an image."""
        if not self.images or page_num > len(self.images):
            logger.error(f"Page {page_num} not available")
            return False
            
        try:
            self.images[page_num-1].save(output_path)
            logger.info(f"Saved page {page_num} as image to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving image: {str(e)}")
            return False
    
    def get_metadata(self):
        """Return the PDF metadata."""
        return self.metadata 