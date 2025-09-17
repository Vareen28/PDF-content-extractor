"""
PDF Understanding Application - Main Program

This application allows you to upload a PDF, extract and understand its content,
and perform various actions with it. It now specializes in handling table of contents
and index documents.
"""

import os
import sys
import json
import argparse
import logging
from pdf_interaction import PDFInteraction

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def display_result(result):
    """Display the result of a command in a user-friendly format."""
    status = result.get("status", "unknown")
    message = result.get("message", "")
    
    if status == "success":
        print(f"\n✅ {message}\n" if message else "\n✅ Success\n")
    else:
        print(f"\n❌ Error: {message}\n" if message else "\n❌ Unknown error\n")
        
    # Special handling for TOC display
    if "display" in result and result["display"]:
        print("Document Structure:")
        print("-" * 50)
        print(result["display"])
        print("-" * 50)
        
    # Special handling for document summary
    if "summary" in result and isinstance(result["summary"], str) and result["summary"]:
        print("Document Summary:")
        print("-" * 50)
        print(result["summary"])
        print("-" * 50)
    
    # Handle auto-detection results
    if "is_toc" in result and result["is_toc"]:
        print("📑 This document was detected as a Table of Contents")
        print("  Use the 'toc' command for more detailed structure analysis")
    elif "is_index" in result and result["is_index"]:
        print("🔍 This document was detected as an Index")
        print("  Use the 'index' command for more detailed entries extraction")
    elif "is_component_list" in result and result["is_component_list"]:
        print("📋 This document was detected as a Component List")
        print("  Use the 'components' command for more detailed component extraction")
    
    # Remove status, message, and already displayed fields from output
    fields_to_remove = ["status", "message", "display", "summary", "auto_processed"]
    clean_result = {k: v for k, v in result.items() if k not in fields_to_remove}
        
    # Pretty print remaining data if there's any
    if clean_result:
        print(json.dumps(clean_result, indent=2, default=str))
        print()

def interactive_mode():
    """Run the application in interactive mode."""
    pdf_system = PDFInteraction()
    
    print("\n=== PDF Understanding Application ===\n")
    print("Specialized for Tables of Contents and Indexes\n")
    print("Type 'help' for available commands or 'exit' to quit.\n")
    
    while True:
        try:
            cmd_input = input("PDF> ").strip()
            
            if not cmd_input:
                continue
                
            if cmd_input.lower() in ['exit', 'quit']:
                print("Exiting application. Goodbye!")
                break
                
            if cmd_input.lower() == 'help':
                show_help()
                continue
                
            # Parse the command
            parts = cmd_input.split(maxsplit=1)
            command = parts[0].lower()
            
            # Parse arguments
            args = {}
            if len(parts) > 1:
                arg_text = parts[1]
                
                # Special case for 'load' command
                if command == 'load':
                    args["path"] = arg_text
                # Special case for 'question' command
                elif command == 'question':
                    args["question"] = arg_text
                # Special case for page and image commands
                elif command in ['page', 'image']:
                    try:
                        args["page"] = int(arg_text)
                    except ValueError:
                        print("❌ Page number must be an integer.")
                        continue
            
            # Process the command
            result = pdf_system.process_command(command, args)
            
            # After loading, if TOC or index is detected, automatically show details
            if command == 'load' and result["status"] == "success":
                if result.get("is_toc", False):
                    # Automatically show TOC details
                    print("\nAutomatically extracting table of contents structure...")
                    toc_result = pdf_system.extract_toc()
                    display_result(toc_result)
                    continue
                elif result.get("is_index", False):
                    # Automatically show index details
                    print("\nAutomatically extracting index entries...")
                    index_result = pdf_system.extract_index()
                    display_result(index_result)
                    continue
                elif result.get("is_component_list", False):
                    # Automatically show component list details
                    print("\nAutomatically extracting component list structure...")
                    components_result = pdf_system.extract_components()
                    display_result(components_result)
                    continue
            
            # Display the result
            display_result(result)
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
        except Exception as e:
            logger.error(f"Error in interactive mode: {str(e)}")
            print(f"\n❌ An error occurred: {str(e)}")
            
def show_help():
    """Display help information."""
    help_text = """
Available commands:

  load <path>          Load a PDF file for processing
  process              Process the loaded PDF (extract text and images)
  analyze              Analyze the PDF content
  toc                  Extract and display table of contents structure
  index                Extract and display index entries
  components           Extract and display structured component lists
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

Special features:
  - PDFs are automatically processed upon loading
  - Table of Contents, Indexes, and Component Lists are automatically detected
  - For TOC/Index/Component List documents, detailed structure is shown automatically
    """
    print(help_text)

def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description="PDF Understanding Application - Specialized for TOC and Index")
    
    # Add subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Interactive mode (default)
    parser_interactive = subparsers.add_parser("interactive", help="Run in interactive mode")
    
    # Load command
    parser_load = subparsers.add_parser("load", help="Load a PDF file")
    parser_load.add_argument("path", help="Path to the PDF file")
    
    # TOC command
    parser_toc = subparsers.add_parser("toc", help="Extract table of contents")
    parser_toc.add_argument("path", help="Path to the PDF file")
    
    # Index command
    parser_index = subparsers.add_parser("index", help="Extract index")
    parser_index.add_argument("path", help="Path to the PDF file")
    
    # Components command
    parser_components = subparsers.add_parser("components", help="Extract component list")
    parser_components.add_argument("path", help="Path to the PDF file")
    
    # Process command
    parser_process = subparsers.add_parser("process", help="Process loaded PDF")
    parser_process.add_argument("path", help="Path to the PDF file")
    
    # Summary command
    parser_summary = subparsers.add_parser("summary", help="Get PDF summary")
    parser_summary.add_argument("path", help="Path to the PDF file")
    
    # Question command
    parser_question = subparsers.add_parser("question", help="Ask a question about the PDF")
    parser_question.add_argument("path", help="Path to the PDF file")
    parser_question.add_argument("question", help="Question to ask")
    
    # Analysis command
    parser_analysis = subparsers.add_parser("analysis", help="Get complete PDF analysis")
    parser_analysis.add_argument("path", help="Path to the PDF file")
    
    return parser.parse_args()

def execute_command(args):
    """Execute a command based on command-line arguments."""
    pdf_system = PDFInteraction()
    
    try:
        # Load the PDF for all commands requiring a path
        if hasattr(args, 'path'):
            result = pdf_system.load_pdf(args.path)
            if result["status"] != "success":
                display_result(result)
                return
        
        # Execute the specific command
        if args.command == "load":
            # Already loaded above, just check if TOC or index
            if result.get("is_toc", False):
                toc_result = pdf_system.extract_toc()
                display_result(toc_result)
            elif result.get("is_index", False):
                index_result = pdf_system.extract_index() 
                display_result(index_result)
            else:
                display_result(result)
        elif args.command == "toc":
            result = pdf_system.extract_toc()
            display_result(result)
        elif args.command == "index":
            result = pdf_system.extract_index()
            display_result(result)
        elif args.command == "components":
            result = pdf_system.extract_components()
            display_result(result)
        elif args.command == "process":
            result = pdf_system.process_pdf()
            display_result(result)
        elif args.command == "summary":
            result = pdf_system.get_pdf_summary()
            display_result(result)
        elif args.command == "question":
            result = pdf_system.answer_question(args.question)
            display_result(result)
        elif args.command == "analysis":
            result = pdf_system.get_full_analysis()
            display_result(result)
        
    except Exception as e:
        logger.error(f"Error executing command: {str(e)}")
        display_result({"status": "error", "message": f"Error: {str(e)}"})

def main():
    """Main entry point of the application."""
    # Parse command-line arguments
    args = parse_arguments()
    
    # If no command specified or interactive mode selected, run interactive mode
    if not args.command or args.command == "interactive":
        interactive_mode()
    else:
        execute_command(args)

if __name__ == "__main__":
    main()
