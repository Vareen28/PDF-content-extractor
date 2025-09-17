#!/usr/bin/env python3
"""
Setup script for PDF Understanding Application
This script helps set up all requirements and dependencies.
"""

import os
import sys
import subprocess
import platform
import shutil
import webbrowser
import site
import tempfile
from pathlib import Path

def print_header(message):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f" {message} ".center(80))
    print("=" * 80 + "\n")

def print_status(message, success=True):
    """Print a status message."""
    if success:
        print(f"✅ {message}")
    else:
        print(f"❌ {message}")

def install_requirements():
    """Install Python package requirements."""
    print_header("Installing Python Requirements")
    
    try:
        # Always install core dependencies explicitly
        core_packages = [
            "PyPDF2",
            "pytesseract",
            "pdfplumber",
            "nltk",
            "reportlab"
        ]
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + core_packages)
        print_status("Successfully installed Python requirements and core dependencies")
        return True
    except subprocess.CalledProcessError:
        print_status("Failed to install requirements or core dependencies", False)
        print("Try running: pip install -r requirements.txt")
        print("Or manually install: pip install PyPDF2 pytesseract pdfplumber nltk reportlab")
        return False

def setup_nltk_data():
    """Download and setup NLTK data."""
    print_header("Setting up NLTK Data")
    
    import nltk
    
    # Create nltk_data directory in user home
    nltk_data_path = os.path.join(os.path.expanduser("~"), "nltk_data")
    os.makedirs(nltk_data_path, exist_ok=True)
    
    # Add the custom path
    nltk.data.path.append(nltk_data_path)
    
    resources = ['punkt', 'stopwords']
    all_success = True
    
    for resource in resources:
        try:
            print(f"Downloading NLTK resource: {resource}...")
            nltk.download(resource, quiet=False, download_dir=nltk_data_path)
            print_status(f"Downloaded {resource}")
        except Exception as e:
            print_status(f"Failed to download {resource}: {str(e)}", False)
            all_success = False
    
    if all_success:
        print_status("Successfully set up NLTK data")
    else:
        print_status("Some NLTK resources could not be downloaded", False)
        print("The application will use fallback methods for text analysis.")
    
    return all_success

def setup_poppler():
    """Help the user install Poppler for PDF image extraction."""
    print_header("Setting up Poppler (for PDF Image Extraction)")
    
    system = platform.system().lower()
    
    # Check if Poppler is already installed
    if shutil.which('pdftoppm') or shutil.which('pdftoppm.exe'):
        print_status("Poppler is already installed")
        return True
    
    if system == 'windows':
        print("Poppler needs to be installed manually on Windows.")
        print("1. Download Poppler for Windows: https://github.com/oschwartz10612/poppler-windows/releases/")
        print("2. Extract the files to a folder (e.g., C:\\Program Files\\poppler)")
        print("3. Add the 'bin' folder to your PATH environment variable")
        
        # Ask if user wants to open the download page
        response = input("Would you like to open the Poppler download page? (y/n): ")
        if response.lower() in ['y', 'yes']:
            webbrowser.open("https://github.com/oschwartz10612/poppler-windows/releases/")
        
        print_status("You will need to install Poppler manually", False)
        return False
        
    elif system == 'darwin':  # macOS
        print("Installing Poppler via Homebrew...")
        try:
            subprocess.run(["brew", "install", "poppler"], check=True)
            print_status("Successfully installed Poppler")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_status("Failed to install Poppler", False)
            print("Try running: brew install poppler")
            return False
            
    elif system == 'linux':
        # Try apt for Debian/Ubuntu
        if shutil.which('apt-get'):
            print("Installing Poppler via apt...")
            try:
                subprocess.run(["sudo", "apt-get", "update"], check=True)
                subprocess.run(["sudo", "apt-get", "install", "-y", "poppler-utils"], check=True)
                print_status("Successfully installed Poppler")
                return True
            except subprocess.CalledProcessError:
                print_status("Failed to install Poppler via apt", False)
                
        # Try yum for RHEL/CentOS/Fedora
        elif shutil.which('yum'):
            print("Installing Poppler via yum...")
            try:
                subprocess.run(["sudo", "yum", "install", "-y", "poppler-utils"], check=True)
                print_status("Successfully installed Poppler")
                return True
            except subprocess.CalledProcessError:
                print_status("Failed to install Poppler via yum", False)
                
        print("Please install Poppler manually:")
        print("- For Debian/Ubuntu: sudo apt-get install poppler-utils")
        print("- For RHEL/CentOS/Fedora: sudo yum install poppler-utils")
        return False
    
    else:
        print_status(f"Unsupported operating system: {system}", False)
        return False

def create_env_file():
    """Create a template .env file for OpenAI API key."""
    print_header("Setting up OpenAI API Integration (Optional)")
    
    env_path = os.path.join(os.getcwd(), '.env')
    
    if os.path.exists(env_path):
        print_status(".env file already exists")
        return True
        
    try:
        with open(env_path, 'w') as f:
            f.write("# OpenAI API key for enhanced PDF analysis\n")
            f.write("# Get your API key from: https://platform.openai.com/account/api-keys\n")
            f.write("OPENAI_API_KEY=your_api_key_here\n")
        
        print_status("Created .env file template")
        print("To enable OpenAI integration:")
        print("1. Edit the .env file")
        print("2. Replace 'your_api_key_here' with your actual OpenAI API key")
        return True
    except Exception as e:
        print_status(f"Failed to create .env file: {str(e)}", False)
        return False

def create_test_pdf():
    """Create a simple test PDF file for testing."""
    print_header("Creating Test PDF")
    
    test_dir = os.path.join(os.getcwd(), 'test_files')
    os.makedirs(test_dir, exist_ok=True)
    test_pdf_path = os.path.join(test_dir, 'test.pdf')
    
    try:
        # Check if reportlab is installed, install if needed
        try:
            import reportlab
        except ImportError:
            print("Installing reportlab for PDF creation...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
        
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        
        c = canvas.Canvas(test_pdf_path, pagesize=letter)
        c.setFont("Helvetica", 12)
        
        # Add some text
        c.drawString(100, 750, "PDF Understanding Application - Test Document")
        c.drawString(100, 730, "-" * 50)
        c.drawString(100, 700, "This is a test PDF file created to verify the functionality")
        c.drawString(100, 680, "of the PDF Understanding Application.")
        c.drawString(100, 650, "You can use this file to test various features:")
        c.drawString(120, 630, "- Text extraction")
        c.drawString(120, 610, "- Summary generation")
        c.drawString(120, 590, "- Topic extraction")
        c.drawString(120, 570, "- Question answering")
        
        # Add more text for better content analysis
        c.drawString(100, 530, "PDF processing technology enables us to extract valuable")
        c.drawString(100, 510, "information from documents, making them searchable and")
        c.drawString(100, 490, "analyzable. This technology is essential for digital")
        c.drawString(100, 470, "transformation initiatives in many organizations.")
        
        c.save()
        
        print_status(f"Created test PDF at: {test_pdf_path}")
        print(f"You can use this file to test the application with the command:")
        print(f"PDF> load {test_pdf_path}")
        return True
    except Exception as e:
        print_status(f"Failed to create test PDF: {str(e)}", False)
        return False

def main():
    """Main setup function."""
    print_header("PDF Understanding Application Setup")
    
    print("This script will help you set up all requirements for the PDF Understanding Application.\n")
    
    # Install Python requirements
    reqs_success = install_requirements()
    
    # Setup NLTK data (after requirements are installed)
    if reqs_success:
        nltk_success = setup_nltk_data()
    else:
        print("Skipping NLTK setup due to requirements installation failure")
        nltk_success = False
    
    # Setup Poppler
    poppler_success = setup_poppler()
    
    # Create .env file
    env_success = create_env_file()
    
    # Create test PDF
    test_pdf_success = create_test_pdf()
    
    # Summary
    print_header("Setup Summary")
    print_status("Python requirements", reqs_success)
    print_status("NLTK data", nltk_success)
    print_status("Poppler (for image extraction)", poppler_success)
    print_status("OpenAI integration setup", env_success)
    print_status("Test PDF creation", test_pdf_success)
    
    print("\nSetup complete! You can now run the application:")
    print("python mainprogram.py")

if __name__ == "__main__":
    main() 