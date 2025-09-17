"""
Table of Contents Extractor - Specialized module for extracting TOC and index entries from PDFs
"""

import re
import logging
from collections import OrderedDict

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TOCEntry:
    """Represents a single TOC entry with level, title, and page number."""
    def __init__(self, level, title, page_num, raw_text=None):
        self.level = level
        self.title = title.strip()
        self.page_num = page_num
        self.raw_text = raw_text
        self.children = []  # For hierarchical TOCs
        
    def __str__(self):
        return f"{' ' * (self.level*2)}{self.title} ({'p.' + str(self.page_num) if self.page_num else 'N/A'})"
        
    def to_dict(self):
        """Convert entry to dictionary representation."""
        result = {
            "level": self.level,
            "title": self.title,
            "page_num": self.page_num
        }
        if self.children:
            result["children"] = [child.to_dict() for child in self.children]
        return result

class IndexEntry:
    """Represents a single index entry with term and page references."""
    def __init__(self, term, page_refs=None, subentries=None):
        self.term = term.strip()
        self.page_refs = page_refs or []
        self.subentries = subentries or {}
        
    def __str__(self):
        page_str = ", ".join([str(p) for p in self.page_refs]) if self.page_refs else "N/A"
        result = f"{self.term}: {page_str}"
        for sub_term, sub_entry in self.subentries.items():
            result += f"\n  {sub_term}: {', '.join([str(p) for p in sub_entry])}"
        return result
        
    def to_dict(self):
        """Convert entry to dictionary representation."""
        result = {
            "term": self.term,
            "page_refs": self.page_refs
        }
        if self.subentries:
            result["subentries"] = {term: pages for term, pages in self.subentries.items()}
        return result

class TOCExtractor:
    """Extract and structure TOC and index information from PDF text."""
    
    def __init__(self):
        """Initialize the TOC extractor."""
        self.toc_entries = []
        self.index_entries = OrderedDict()
        self.toc_patterns = self._compile_toc_patterns()
        self.index_patterns = self._compile_index_patterns()
        
    def _compile_toc_patterns(self):
        """Compile regex patterns for TOC extraction."""
        patterns = [
            # Pattern 1: Classic TOC pattern with dots
            # e.g. "1. Introduction..............10"
            re.compile(r'(?P<prefix>(?:\d+\.)+\s*)?(?P<title>.*?)\.{2,}(?P<page>\d+)$'),
            
            # Pattern 2: TOC with numbers without dots
            # e.g. "1. Introduction 10" or "Chapter 1. Introduction 10"
            re.compile(r'(?P<prefix>(?:(?:Chapter|Section|Part)\s+)?\d+\.?\s+)?(?P<title>.*?)\s+(?P<page>\d+)$'),
            
            # Pattern 3: TOC with Roman numerals
            # e.g. "I. Introduction 10"
            re.compile(r'(?P<prefix>[IVXivx]+\.?\s+)?(?P<title>.*?)\s+(?P<page>\d+)$'),
            
            # Pattern 4: TOC with alphanumeric identifiers
            # e.g. "A.1 Introduction 10"
            re.compile(r'(?P<prefix>[A-Z](?:\.\d+)+\s+)?(?P<title>.*?)\s+(?P<page>\d+)$'),
            
            # Pattern 5: Indented TOC without numbering
            # e.g. "    Introduction..............10"
            re.compile(r'^(?P<indent>\s{2,})(?P<title>.*?)\.{2,}(?P<page>\d+)$'),
            
            # Pattern 6: Indented TOC without dots
            # e.g. "    Introduction 10"
            re.compile(r'^(?P<indent>\s{2,})(?P<title>.*?)\s+(?P<page>\d+)$')
        ]
        return patterns
    
    def _compile_index_patterns(self):
        """Compile regex patterns for index extraction."""
        patterns = [
            # Pattern 1: Term with page number(s)
            # e.g. "Algorithms, 10, 15-17, 23"
            re.compile(r'(?P<term>.*?),\s*(?P<pages>(?:\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*))$'),
            
            # Pattern 2: Indented subentry
            # e.g. "    recursive, 15, 17"
            re.compile(r'^\s{2,}(?P<subterm>.*?),\s*(?P<pages>(?:\d+(?:-\d+)?(?:,\s*\d+(?:-\d+)?)*))$'),
            
            # Pattern 3: Term with see reference
            # e.g. "Sorting, see Algorithms"
            re.compile(r'(?P<term>.*?),\s*see\s+(?P<reference>.*?)$', re.IGNORECASE),
            
            # Pattern 4: Term with See also reference
            # e.g. "Algorithms. See also Machine Learning"
            re.compile(r'(?P<term>.*?)\.\s*See\s+also\s+(?P<reference>.*?)$', re.IGNORECASE)
        ]
        return patterns
        
    def extract_toc_from_text(self, text, is_index=False):
        """Extract TOC or index entries from text."""
        if is_index:
            return self._extract_index(text)
        else:
            return self._extract_toc(text)
            
    def _extract_toc(self, text):
        """Extract Table of Contents entries from text."""
        self.toc_entries = []
        lines = text.split('\n')
        
        # First pass - identify TOC entries
        for line_num, line in enumerate(lines):
            line = line.rstrip()
            if not line.strip():
                continue
                
            # Skip obvious non-TOC lines like headers/footers
            if len(line.strip()) < 5:
                continue
                
            entry = self._parse_toc_line(line)
            if entry:
                self.toc_entries.append(entry)
                
        # Second pass - determine hierarchy
        if self.toc_entries:
            self._determine_hierarchy()
                
        logger.info(f"Extracted {len(self.toc_entries)} TOC entries")
        return self.toc_entries
        
    def _parse_toc_line(self, line):
        """Parse a single line of text to extract TOC information."""
        # Try all patterns
        for pattern in self.toc_patterns:
            match = pattern.match(line)
            if match:
                groups = match.groupdict()
                
                # Extract title
                title = groups.get('title', '').strip()
                
                # Extract page number
                page_num = None
                if 'page' in groups and groups['page']:
                    try:
                        page_num = int(groups['page'])
                    except ValueError:
                        pass
                
                # Determine level based on prefix, indent, or position
                level = 0
                if 'prefix' in groups and groups['prefix']:
                    # Count dots or depth indicators
                    prefix = groups['prefix'].strip()
                    level = prefix.count('.') 
                    if level == 0 and prefix:  # If no dots but has prefix
                        level = 1
                elif 'indent' in groups and groups['indent']:
                    # Determine level by indentation
                    level = len(groups['indent']) // 2
                
                if title:  # Skip if no title extracted
                    return TOCEntry(level, title, page_num, line)
        
        # Last resort - look for page numbers at the end
        page_match = re.search(r'(\S+)\s+(\d+)$', line)
        if page_match:
            try:
                title = line[:page_match.start()].strip()
                page_num = int(page_match.group(2))
                # Guess level based on indentation
                leading_spaces = len(line) - len(line.lstrip())
                level = leading_spaces // 2
                return TOCEntry(level, title, page_num, line)
            except:
                pass
                
        return None
        
    def _determine_hierarchy(self):
        """Determine hierarchical relationships between TOC entries."""
        # Sort by level and position
        self.toc_entries.sort(key=lambda x: (x.level, self.toc_entries.index(x)))
        
        # Build hierarchy
        hierarchy = []
        last_by_level = {0: None}
        
        for entry in self.toc_entries:
            if entry.level == 0:
                hierarchy.append(entry)
                last_by_level[0] = entry
            else:
                # Find parent (closest entry with level one less than current)
                parent_level = entry.level - 1
                while parent_level >= 0:
                    if parent_level in last_by_level and last_by_level[parent_level]:
                        last_by_level[parent_level].children.append(entry)
                        break
                    parent_level -= 1
                if parent_level < 0:  # No parent found, add to root
                    hierarchy.append(entry)
                    
                last_by_level[entry.level] = entry
        
        # Update entries with new hierarchy
        self.toc_entries = hierarchy
        
        return hierarchy
        
    def _extract_index(self, text):
        """Extract index entries from text."""
        self.index_entries = OrderedDict()
        lines = text.split('\n')
        
        current_main_term = None
        
        for line_num, line in enumerate(lines):
            line = line.rstrip()
            if not line.strip():
                continue
                
            # Check for main entry patterns
            main_entry_match = None
            for pattern in self.index_patterns[:1]:  # Use first pattern for main entries
                match = pattern.match(line)
                if match:
                    main_entry_match = match
                    break
                    
            # If main entry found
            if main_entry_match:
                groups = main_entry_match.groupdict()
                term = groups.get('term', '').strip()
                pages_str = groups.get('pages', '')
                
                if term:
                    # Parse page numbers
                    page_refs = self._parse_page_refs(pages_str)
                    
                    # Create entry
                    self.index_entries[term] = IndexEntry(term, page_refs)
                    current_main_term = term
                    
            # Check for subentry pattern
            elif current_main_term and line.startswith(' '):
                subentry_match = None
                for pattern in self.index_patterns[1:2]:  # Use pattern for subentries
                    match = pattern.match(line)
                    if match:
                        subentry_match = match
                        break
                        
                if subentry_match:
                    groups = subentry_match.groupdict()
                    subterm = groups.get('subterm', '').strip()
                    pages_str = groups.get('pages', '')
                    
                    if subterm:
                        # Parse page numbers
                        page_refs = self._parse_page_refs(pages_str)
                        
                        # Add to main entry
                        main_entry = self.index_entries[current_main_term]
                        main_entry.subentries[subterm] = page_refs
                        
        logger.info(f"Extracted {len(self.index_entries)} index entries")
        return list(self.index_entries.values())
        
    def _parse_page_refs(self, pages_str):
        """Parse page references from string, including ranges."""
        if not pages_str:
            return []
            
        page_refs = []
        chunks = [p.strip() for p in pages_str.split(',')]
        
        for chunk in chunks:
            if '-' in chunk:  # Page range
                try:
                    start, end = chunk.split('-')
                    start, end = int(start), int(end)
                    page_refs.extend(range(start, end + 1))
                except:
                    # If parsing fails, add as is
                    page_refs.append(chunk)
            else:
                try:
                    page_refs.append(int(chunk))
                except:
                    # If not a number, add as is
                    if chunk:
                        page_refs.append(chunk)
                        
        return page_refs
        
    def get_toc_structure(self):
        """Get the hierarchical TOC structure as a list of dictionaries."""
        return [entry.to_dict() for entry in self.toc_entries]
        
    def get_index_structure(self):
        """Get the index structure as a list of dictionaries."""
        return [entry.to_dict() for entry in self.index_entries.values()]
        
    def display_toc(self):
        """Return a formatted string representation of the TOC."""
        output = []
        
        def _format_entry(entry, indent=0):
            output.append(f"{' ' * indent}{entry}")
            for child in entry.children:
                _format_entry(child, indent + 2)
                
        for entry in self.toc_entries:
            _format_entry(entry)
            
        return "\n".join(output)
        
    def display_index(self):
        """Return a formatted string representation of the index."""
        output = []
        
        for entry in self.index_entries.values():
            output.append(str(entry))
            
        return "\n".join(output)
        
    def summarize_document_structure(self):
        """Generate a summary of the document structure based on TOC."""
        if not self.toc_entries:
            return "No table of contents found."
            
        num_sections = len(self.toc_entries)
        max_depth = 0
        
        def get_depth(entry, current_depth=1):
            if not entry.children:
                return current_depth
            return max(get_depth(child, current_depth + 1) for child in entry.children)
            
        for entry in self.toc_entries:
            depth = get_depth(entry)
            if depth > max_depth:
                max_depth = depth
                
        # Collect all pages referenced
        pages = []
        
        def collect_pages(entry):
            if entry.page_num:
                pages.append(entry.page_num)
            for child in entry.children:
                collect_pages(child)
                
        for entry in self.toc_entries:
            collect_pages(entry)
            
        # Sort and find range
        if pages:
            pages.sort()
            min_page = min(pages)
            max_page = max(pages)
            page_range = f"{min_page}-{max_page}"
        else:
            page_range = "unknown"
            
        summary = f"Document contains {num_sections} main sections with {max_depth} levels of depth.\n"
        summary += f"Page range covered in TOC: {page_range}\n"
        summary += f"Top-level sections:\n"
        
        for i, entry in enumerate(self.toc_entries):
            summary += f"  {i+1}. {entry.title}"
            if entry.page_num:
                summary += f" (p.{entry.page_num})"
            summary += "\n"
            
        return summary 