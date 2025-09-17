"""
PDF Interaction Module - Handles user interaction with PDF content
"""

import os
import json
import logging
import re
from pdf_processor import PDFProcessor
from pdf_analyzer import PDFAnalyzer
from toc_extractor import TOCExtractor
from component_extractor import ComponentExtractor

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDFInteraction:
    def __init__(self):
        """Initialize the PDF interaction system."""
        self.processor = PDFProcessor()
        self.analyzer = PDFAnalyzer()
        self.toc_extractor = TOCExtractor()
        self.component_extractor = ComponentExtractor()
        self.pdf_path = None
        self.processed = False
        self.analyzed = False
        self.toc_extracted = False
        self.components_extracted = False
        self.history = []
        self.index_detected = False
        self.toc_detected = False
        self.components_detected = False
        
    def load_pdf(self, pdf_path):
        """Load a PDF for processing and analysis."""
        try:
            # Convert to absolute path and normalize
            pdf_path = os.path.abspath(pdf_path)
            
            # Check if file exists
            if not os.path.exists(pdf_path):
                return {"status": "error", "message": f"File not found: {pdf_path}"}
            
            # Check if it's a file (not a directory)
            if not os.path.isfile(pdf_path):
                return {"status": "error", "message": f"Path is not a file: {pdf_path}"}
            
            # Check file extension
            if not pdf_path.lower().endswith('.pdf'):
                return {"status": "error", "message": "File must be a PDF document"}
            
            # Check read permissions
            if not os.access(pdf_path, os.R_OK):
                return {"status": "error", "message": f"No read permission for file: {pdf_path}"}
            
            # Reset state
            self.pdf_path = pdf_path
            self.processed = False
            self.analyzed = False
            self.toc_extracted = False
            self.components_extracted = False
            self.index_detected = False
            self.toc_detected = False
            self.components_detected = False
            
            # Load the PDF
            success = self.processor.load_pdf(pdf_path)
            if not success:
                return {"status": "error", "message": "Failed to load PDF"}
                
            # Add to history
            self.add_to_history("load", f"Loaded PDF: {os.path.basename(pdf_path)}")

            # Automatically process the PDF after loading
            process_result = self.process_pdf()
            
            if process_result["status"] == "success":
                # Automatically detect if this is a TOC/index and analyze
                detection_result = self.detect_pdf_type()
                
                # Include detection information in the result
                load_message = f"PDF loaded: {os.path.basename(pdf_path)}"
                if self.toc_detected:
                    load_message += " (Table of Contents detected)"
                elif self.index_detected:
                    load_message += " (Index detected)"
                elif self.components_detected:
                    load_message += " (Component List detected)"
                
                return {
                    "status": "success", 
                    "message": load_message,
                    "auto_processed": True,
                    "is_toc": self.toc_detected,
                    "is_index": self.index_detected,
                    "is_component_list": self.components_detected,
                    "pages": self.processor.total_pages
                }
            else:
                # Just return success for loading even if processing failed
                return {"status": "success", "message": f"PDF loaded: {os.path.basename(pdf_path)}"}
                
        except PermissionError as e:
            logger.error(f"Permission error loading PDF: {str(e)}")
            return {"status": "error", "message": f"Permission denied: {str(e)}"}
        except Exception as e:
            logger.error(f"Error loading PDF: {str(e)}")
            return {"status": "error", "message": f"Error loading PDF: {str(e)}"}
    
    def process_pdf(self):
        """Process the loaded PDF for text and images."""
        if not self.pdf_path:
            return {"status": "error", "message": "No PDF loaded"}
            
        try:
            # Extract text from PDF
            text_success = self.processor.extract_text()
            if not text_success:
                return {"status": "error", "message": "Failed to extract text from PDF"}
                
            # Try OCR if some pages have little or no text
            has_empty_pages = any(len(text.strip()) < 50 for page, text in self.processor.text_content.items())
            if has_empty_pages:
                logger.info("Some pages have little text, trying OCR...")
                self.processor.ocr_pdf()
                
            # Extract images if poppler is available
            if self.processor.poppler_available:
                self.processor.extract_images()
            else:
                logger.warning("Skipping image extraction as Poppler is not available")
            
            # Set the full text for analysis
            all_text = self.processor.get_all_text()
            self.analyzer.set_text(all_text)
            
            # Mark as processed
            self.processed = True
            
            # Add to history
            self.add_to_history("process", "Processed PDF for text and images")
            
            return {
                "status": "success", 
                "message": "PDF processed successfully",
                "pages": self.processor.total_pages,
                "text_extracted": bool(all_text.strip())
            }
        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            return {"status": "error", "message": f"Error processing PDF: {str(e)}"}
            
    def detect_pdf_type(self):
        """Detect if the PDF is a table of contents or index."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            all_text = self.processor.get_all_text()
            
            # Check for TOC patterns
            # Look for TOC markers in the text
            toc_markers = [
                'table of contents',
                'contents',
                'toc',
                'chapter',
                'section'
            ]
            
            # Look for Index markers
            index_markers = [
                'index',
                'subject index',
                'keyword index',
                'alphabetical index'
            ]
            
            # Look for Component List markers
            component_markers = [
                'course file',
                'checklist',
                'components',
                'inventory',
                'file index'
            ]
            
            # Check if these markers appear in the first few paragraphs
            first_500_chars = all_text[:500].lower()
            
            is_toc = any(marker in first_500_chars for marker in toc_markers)
            is_index = any(marker in first_500_chars for marker in index_markers)
            is_component_list = any(marker in first_500_chars for marker in component_markers)
            
            # If not detected in the first characters, try to determine by content patterns
            if not is_toc and not is_index and not is_component_list:
                # Extract TOC entries
                toc_entries = self.toc_extractor.extract_toc_from_text(all_text)
                
                # If we found a significant number of TOC entries, it's likely a TOC
                if len(toc_entries) > 5:
                    is_toc = True
                    
                # If not TOC, check for index patterns
                if not is_toc:
                    index_entries = self.toc_extractor.extract_toc_from_text(all_text, is_index=True)
                    if len(index_entries) > 5:
                        is_index = True
                        
                # If not TOC or index, check for component list patterns
                if not is_toc and not is_index:
                    # Look for numbered lists with consistent formatting
                    components = self.component_extractor.extract_components_from_text(all_text)
                    if len(components) > 5:
                        is_component_list = True
            
            self.toc_detected = is_toc
            self.index_detected = is_index
            self.components_detected = is_component_list
            self.toc_extracted = True
            
            # Add to history
            if is_toc:
                self.add_to_history("detect", "Detected Table of Contents")
            elif is_index:
                self.add_to_history("detect", "Detected Index")
            elif is_component_list:
                self.add_to_history("detect", "Detected Component List")
            else:
                self.add_to_history("detect", "Document type not determined")
            
            return {
                "status": "success",
                "is_toc": is_toc,
                "is_index": is_index,
                "is_component_list": is_component_list
            }
        except Exception as e:
            logger.error(f"Error detecting PDF type: {str(e)}")
            return {"status": "error", "message": f"Error detecting PDF type: {str(e)}"}
    
    def analyze_pdf(self):
        """Analyze the processed PDF content."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            # Run analysis
            self.analyzer.preprocess_text()
            self.analyzer.extract_keywords()
            summary = self.analyzer.generate_summary()
            topics = self.analyzer.extract_topics()
            
            # Mark as analyzed
            self.analyzed = True
            
            # Add to history
            self.add_to_history("analyze", "Analyzed PDF content")
            
            return {
                "status": "success",
                "message": "PDF analyzed successfully",
                "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                "keywords": self.analyzer.keywords[:5]
            }
        except Exception as e:
            logger.error(f"Error analyzing PDF: {str(e)}")
            return {"status": "error", "message": f"Error analyzing PDF: {str(e)}"}
    
    def extract_toc(self, reprocess=False):
        """Extract table of contents from the PDF."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            all_text = self.processor.get_all_text()
            
            # Extract TOC using the specialized extractor
            toc_entries = self.toc_extractor.extract_toc_from_text(all_text)
            
            # Mark as extracted
            self.toc_extracted = True
            
            # Add to history
            self.add_to_history("toc", f"Extracted {len(toc_entries)} TOC entries")
            
            # Format TOC for display
            toc_display = self.toc_extractor.display_toc()
            
            # Get document structure summary
            doc_summary = self.toc_extractor.summarize_document_structure()
            
            return {
                "status": "success",
                "message": f"Extracted {len(toc_entries)} TOC entries",
                "entries": self.toc_extractor.get_toc_structure(),
                "display": toc_display,
                "summary": doc_summary
            }
        except Exception as e:
            logger.error(f"Error extracting TOC: {str(e)}")
            return {"status": "error", "message": f"Error extracting TOC: {str(e)}"}
            
    def extract_index(self):
        """Extract index entries from the PDF."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            all_text = self.processor.get_all_text()
            
            # Extract index entries
            index_entries = self.toc_extractor.extract_toc_from_text(all_text, is_index=True)
            
            # Add to history
            self.add_to_history("index", f"Extracted {len(index_entries)} index entries")
            
            # Format index for display
            index_display = self.toc_extractor.display_index()
            
            return {
                "status": "success",
                "message": f"Extracted {len(index_entries)} index entries",
                "entries": self.toc_extractor.get_index_structure(),
                "display": index_display
            }
        except Exception as e:
            logger.error(f"Error extracting index: {str(e)}")
            return {"status": "error", "message": f"Error extracting index: {str(e)}"}
    
    def get_pdf_summary(self):
        """Get a summary of the PDF content."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if not self.analyzed:
                self.analyze_pdf()
                
            summary = self.analyzer.summary
            if not summary:
                summary = self.analyzer.generate_summary()
                
            # Add to history
            self.add_to_history("summary", "Retrieved PDF summary")
            
            return {
                "status": "success",
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error getting summary: {str(e)}")
            return {"status": "error", "message": f"Error getting summary: {str(e)}"}
    
    def get_pdf_topics(self):
        """Get main topics from the PDF content."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if not self.analyzed:
                self.analyze_pdf()
                
            topics = self.analyzer.topics
            if not topics:
                topics = self.analyzer.extract_topics()
                
            # Add to history
            self.add_to_history("topics", "Retrieved PDF topics")
            
            return {
                "status": "success",
                "topics": topics
            }
        except Exception as e:
            logger.error(f"Error getting topics: {str(e)}")
            return {"status": "error", "message": f"Error getting topics: {str(e)}"}
    
    def answer_question(self, question):
        """Answer a question about the PDF content."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if not self.analyzer.sentences:
                self.analyzer.preprocess_text()
                
            answer = self.analyzer.answer_question(question)
            
            # Add to history
            self.add_to_history("question", f"Q: {question[:30]}...")
            
            return {
                "status": "success",
                "question": question,
                "answer": answer
            }
        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return {"status": "error", "message": f"Error answering question: {str(e)}"}
    
    def extract_page_text(self, page_num):
        """Get the text content of a specific page."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if page_num < 1 or page_num > self.processor.total_pages:
                return {"status": "error", "message": f"Invalid page number: {page_num}"}
                
            text = self.processor.get_text_by_page(page_num)
            
            # Add to history
            self.add_to_history("page", f"Retrieved text from page {page_num}")
            
            return {
                "status": "success",
                "page": page_num,
                "text": text
            }
        except Exception as e:
            logger.error(f"Error getting page text: {str(e)}")
            return {"status": "error", "message": f"Error getting page text: {str(e)}"}
    
    def save_page_image(self, page_num, output_path=None):
        """Save a page as an image."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if page_num < 1 or page_num > self.processor.total_pages:
                return {"status": "error", "message": f"Invalid page number: {page_num}"}
                
            # Generate output path if not provided
            if not output_path:
                pdf_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
                output_dir = os.path.join(os.path.dirname(self.pdf_path), "pdf_images")
                os.makedirs(output_dir, exist_ok=True)
                output_path = os.path.join(output_dir, f"{pdf_name}_page_{page_num}.png")
                
            # Save the image
            success = self.processor.save_image(page_num, output_path)
            if not success:
                return {"status": "error", "message": "Failed to save image"}
                
            # Add to history
            self.add_to_history("image", f"Saved page {page_num} as image")
            
            return {
                "status": "success",
                "page": page_num,
                "image_path": output_path
            }
        except Exception as e:
            logger.error(f"Error saving page image: {str(e)}")
            return {"status": "error", "message": f"Error saving page image: {str(e)}"}
    
    def get_pdf_metadata(self):
        """Get metadata from the PDF."""
        if not self.pdf_path:
            return {"status": "error", "message": "No PDF loaded"}
            
        try:
            metadata = self.processor.get_metadata()
            
            # Add to history
            self.add_to_history("metadata", "Retrieved PDF metadata")
            
            return {
                "status": "success",
                "metadata": metadata
            }
        except Exception as e:
            logger.error(f"Error getting metadata: {str(e)}")
            return {"status": "error", "message": f"Error getting metadata: {str(e)}"}
    
    def get_full_analysis(self):
        """Get a complete analysis of the PDF."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            if not self.analyzed:
                self.analyze_pdf()
                
            analysis = self.analyzer.get_analysis_results()
            
            # Add metadata
            analysis["metadata"] = self.processor.get_metadata()
            
            # Add file info
            analysis["file_info"] = {
                "filename": os.path.basename(self.pdf_path),
                "path": self.pdf_path,
                "pages": self.processor.total_pages,
                "size": os.path.getsize(self.pdf_path)
            }
            
            # Add to history
            self.add_to_history("full_analysis", "Retrieved complete PDF analysis")
            
            return {
                "status": "success",
                "analysis": analysis
            }
        except Exception as e:
            logger.error(f"Error getting full analysis: {str(e)}")
            return {"status": "error", "message": f"Error getting full analysis: {str(e)}"}
    
    def add_to_history(self, action_type, description):
        """Add an action to the history."""
        import datetime
        
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "action": action_type,
            "description": description
        }
        
        self.history.append(entry)
    
    def get_history(self):
        """Get the interaction history."""
        return {"status": "success", "history": self.history}
    
    def create_component_folders(self):
        """Create folders for each component where teachers can store related PDFs."""
        if not self.components_extracted:
            return {"status": "error", "message": "Components not extracted yet. Please run 'components' command first."}
            
        try:
            # Create a base directory for component folders
            base_dir = "course_components"
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
                
            # Create folders for each component
            created_folders = []
            for component in self.component_extractor.components:
                # Create a safe folder name from the component title
                folder_name = re.sub(r'[<>:"/\\|?*]', '_', component.title)
                folder_name = re.sub(r'\s+', '_', folder_name)
                folder_path = os.path.join(base_dir, f"{component.number}_{folder_name}")
                
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                    created_folders.append(folder_path)
                    
                    # Create a README.txt in each folder with component details
                    with open(os.path.join(folder_path, "README.txt"), "w", encoding="utf-8") as f:
                        f.write(f"Component {component.number}: {component.title}\n")
                        if component.description:
                            f.write(f"\nDescription: {component.description}\n")
                        f.write("\nUpload related PDFs for this component in this folder.")
            
            return {
                "status": "success",
                "message": f"Created {len(created_folders)} component folders in '{base_dir}' directory.",
                "folders": created_folders
            }
            
        except Exception as e:
            logger.error(f"Error creating component folders: {str(e)}")
            return {"status": "error", "message": f"Error creating folders: {str(e)}"}
    
    def process_command(self, command, args=None):
        """Process a user command with arguments."""
        if args is None:
            args = {}
            
        # Command mapping
        command_map = {
            "load": lambda: self.load_pdf(args.get("path")),
            "process": self.process_pdf,
            "analyze": self.analyze_pdf,
            "toc": self.extract_toc,
            "index": self.extract_index,
            "components": self.extract_components,
            "detect": self.detect_pdf_type,
            "summary": self.get_pdf_summary,
            "topics": self.get_pdf_topics,
            "question": lambda: self.answer_question(args.get("question")),
            "page": lambda: self.extract_page_text(int(args.get("page", 1))),
            "image": lambda: self.save_page_image(int(args.get("page", 1)), args.get("output")),
            "metadata": self.get_pdf_metadata,
            "analysis": self.get_full_analysis,
            "history": self.get_history,
            "create_folders": self.create_component_folders
        }
        
        # Check if command exists
        if command not in command_map:
            return {"status": "error", "message": f"Unknown command: {command}"}
            
        # Execute the command
        return command_map[command]()
    
    def extract_components(self):
        """Extract structured components from the PDF."""
        if not self.processed:
            return {"status": "error", "message": "PDF not processed yet"}
            
        try:
            all_text = self.processor.get_all_text()
            
            # Extract components using the specialized extractor
            components = self.component_extractor.extract_components_from_text(all_text)
            
            # Organize components into categories
            categories = self.component_extractor.organize_by_categories()
            
            # Get formatted display
            display = self.component_extractor.display_components()
            
            # Generate a summary
            summary = self.component_extractor.summarize_components()
            
            # Mark as extracted
            self.components_extracted = True
            
            # Add to history
            self.add_to_history("components", f"Extracted {len(components)} components")
            
            return {
                "status": "success",
                "message": f"Extracted {len(components)} components from PDF",
                "components": self.component_extractor.get_components_structure(),
                "categories": self.component_extractor.get_categories_structure(),
                "display": display,
                "summary": summary
            }
        except Exception as e:
            logger.error(f"Error extracting components: {str(e)}")
            return {"status": "error", "message": f"Error extracting components: {str(e)}"} 