#!/usr/bin/env python3
import os
import mimetypes
from typing import Set, Dict, Optional, Tuple
from rich.console import Console

console = Console()

# Common binary file extensions
BINARY_EXTENSIONS = {
    # Executables
    '.exe', '.dll', '.so', '.dylib', '.bin',
    # Images
    '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico', '.svg',
    # Documents
    '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
    # Archives
    '.zip', '.tar', '.gz', '.rar', '.7z',
    # Media
    '.mp3', '.mp4', '.avi', '.mov', '.wav',
    # Other
    '.db', '.sqlite', '.dat', '.bin'
}

# MIME types that should be treated as text
TEXT_MIME_TYPES = {
    'text/',
    'application/json',
    'application/xml',
    'application/javascript',
    'application/x-python',
    'application/x-shellscript',
    'application/x-php',
    'application/x-ruby',
    'application/x-java',
    'application/x-c',
    'application/x-c++',
    'application/x-csharp',
    'application/x-typescript',
    'application/x-html',
    'application/x-css',
    'application/x-yaml',
    'application/x-toml',
    'application/x-markdown',
    'application/x-csv',
    'application/x-tex',
    'application/x-latex',
    'application/x-rst',
    'application/x-asciidoc',
    'application/x-org',
    'application/x-org-mode',
    'application/x-org-mode+org',
    'application/x-org-mode+txt',
    'application/x-org-mode+text',
    'application/x-org-mode+plain',
    'application/x-org-mode+markdown',
    'application/x-org-mode+md',
    'application/x-org-mode+rst',
    'application/x-org-mode+asciidoc',
    'application/x-org-mode+adoc',
    'application/x-org-mode+org-mode',
    'application/x-org-mode+orgmode',
    'application/x-org-mode+orgmode-mode',
    'application/x-org-mode+orgmode-mode-mode',
}

def get_mime_type(file_path: str) -> Optional[str]:
    """Get MIME type of a file using python-magic or mimetypes."""
    try:
        import magic
        mime = magic.from_file(file_path, mime=True)
    except (ImportError, Exception):
        # Fallback to mimetypes if python-magic is not available
        mime, _ = mimetypes.guess_type(file_path)
    
    return mime

def is_binary_file(file_path: str) -> bool:
    """
    Check if a file is binary using multiple methods:
    1. File extension
    2. MIME type
    3. Content inspection (if needed)
    """
    # Check extension first (fastest)
    ext = os.path.splitext(file_path)[1].lower()
    if ext in BINARY_EXTENSIONS:
        return True
    
    # Check MIME type
    mime = get_mime_type(file_path)
    if mime is None:
        return True  # Unknown MIME type, treat as binary
    
    # Check if it's a known text MIME type
    if any(mime.startswith(prefix) for prefix in TEXT_MIME_TYPES):
        return False
    
    # If we get here, it's probably binary
    return True

def get_file_info(file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get comprehensive file information.
    Returns: (is_binary, mime_type, language)
    """
    mime = get_mime_type(file_path)
    is_binary = is_binary_file(file_path)
    
    # Try to determine language from MIME type
    language = None
    if mime:
        if 'python' in mime:
            language = 'Python'
        elif 'javascript' in mime:
            language = 'JavaScript'
        elif 'shellscript' in mime:
            language = 'Shell'
        elif 'php' in mime:
            language = 'PHP'
        elif 'ruby' in mime:
            language = 'Ruby'
        elif 'java' in mime:
            language = 'Java'
        elif 'c' in mime:
            language = 'C'
        elif 'c++' in mime:
            language = 'C++'
        elif 'csharp' in mime:
            language = 'C#'
        elif 'typescript' in mime:
            language = 'TypeScript'
        elif 'html' in mime:
            language = 'HTML'
        elif 'css' in mime:
            language = 'CSS'
        elif 'yaml' in mime:
            language = 'YAML'
        elif 'toml' in mime:
            language = 'TOML'
        elif 'markdown' in mime:
            language = 'Markdown'
        elif 'csv' in mime:
            language = 'CSV'
        elif 'tex' in mime or 'latex' in mime:
            language = 'LaTeX'
        elif 'rst' in mime:
            language = 'RST'
        elif 'asciidoc' in mime:
            language = 'AsciiDoc'
        elif 'org' in mime:
            language = 'Org'
    
    return is_binary, mime, language 