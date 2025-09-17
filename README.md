# PDF Understanding Application

This application allows you to upload a PDF file, extract and understand its content, and perform various actions with it. It's now specialized in handling **table of contents (TOC)** and **index documents**.

## Features

- Automatic detection of table of contents and index documents
- Extraction and structured representation of TOC entries and hierarchies
- Extraction of index entries with page references
- PDF text extraction and analysis
- Image extraction from PDFs
- Text analysis and summarization
- Question answering about the PDF content
- Content navigation and search

## Quick Setup

For the easiest setup experience, run the setup script:

```
python setup.py
```

This script will:
1. Install all required Python packages
2. Download necessary NLTK data
3. Help you install Poppler (required for image extraction)
4. Create a template `.env` file for OpenAI integration
5. Create a test PDF file for you to try the application

## Manual Setup

If you prefer to set up manually:

1. Install the requirements:
```
pip install -r requirements.txt
```

2. Install external dependencies:
   - **Tesseract OCR** (for image-to-text conversion)
     - For Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
     - For macOS: `brew install tesseract`
     - For Linux: `sudo apt-get install tesseract-ocr`
   
   - **Poppler** (for PDF image extraction)
     - For Windows: Download from https://github.com/oschwartz10612/poppler-windows/releases/
     - For macOS: `brew install poppler`
     - For Linux: `sudo apt-get install poppler-utils`

3. Set up NLTK data:
   ```python
   import nltk
   nltk.download('punkt')
   nltk.download('stopwords')
   ```

4. OpenAI API (Optional for enhanced analysis):
   - Create a `.env` file with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

## Usage

Run the main program:
```
python mainprogram.py
```

### Interactive Mode Commands

The application supports the following commands in interactive mode:

```
load <path>          Load a PDF file for processing
process              Process the loaded PDF (extract text and images)
analyze              Analyze the PDF content
toc                  Extract and display table of contents structure
index                Extract and display index entries  
detect               Detect if the document is a TOC or index
summary              Get a summary of the PDF content
topics               Extract main topics from the PDF
question <text>      Ask a question about the PDF content
page <number>        Get text from a specific page
image <number>       Save a specific page as an image
metadata             Get PDF metadata
analysis             Get a complete analysis of the PDF
history              View the history of actions
help                 Show this help message
exit                 Exit the application
```

## Uploading PDFs

To upload a PDF, use the `load` command followed by the path to your PDF file:

```
PDF> load path/to/your/document.pdf
```

For example:
```
PDF> load C:\Users\Documents\sample.pdf
```

When you load a PDF:
1. The document is automatically processed
2. The system detects if it's a table of contents or index
3. For TOC/index documents, the structure is automatically extracted and displayed

Make sure to:
- Use the full path if the PDF is not in the current directory
- Use quotes if your path contains spaces: `load "C:\My Documents\sample.pdf"`
- Ensure you have read permissions for the file
- Verify the file is a valid PDF document

## Working with Table of Contents

The application automatically detects if a document is a table of contents. For TOC documents:

1. The structure is hierarchically organized
2. Entries are displayed with their page numbers
3. Document structure summary is provided

You can manually extract TOC with:
```
PDF> toc
```

## Working with Indexes

For index documents, the application:

1. Extracts main entries with their page references
2. Identifies subentries when present
3. Handles page ranges (e.g., "10-15")

You can manually extract index entries with:
```
PDF> index
```

## Troubleshooting

### Permission Errors
If you get "Permission denied" errors when loading PDFs:
- Make sure you have read permissions for the file
- Try running the application as administrator
- Use a different directory for your PDF files (e.g., in your user directory)

### NLTK Data Errors
If you see errors about missing NLTK data:
- Run the setup script: `python setup.py`
- Or manually download the required resources:
  ```python
  import nltk
  nltk.download('punkt')
  nltk.download('stopwords')
  ```

### Image Extraction Errors
If you see "Unable to get page count. Is poppler installed and in PATH?":
- Install Poppler (see setup instructions above)
- Add Poppler's bin directory to your system PATH
- The application will still work for text analysis without Poppler

## Files

- `mainprogram.py`: Main entry point
- `pdf_processor.py`: PDF extraction and processing
- `pdf_analyzer.py`: Text analysis and understanding
- `pdf_interaction.py`: Interface for interacting with PDF content
- `toc_extractor.py`: Specialized module for TOC and index extraction
- `setup.py`: Setup script for dependencies 