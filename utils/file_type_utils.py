#!/usr/bin/env python3
import os
import mimetypes
from typing import Set, Dict, Optional, Tuple
from rich.console import Console
import magic
from pathlib import Path
from .language_detector import detect_language, get_language_stats

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

def get_mime_type(file_path: Path) -> str:
    """Get the MIME type of a file.
    
    Args:
        file_path: Path to the file
        
    Returns:
        MIME type string
    """
    return magic.from_file(str(file_path), mime=True)

def is_binary_file(file_path: Path) -> bool:
    """Check if a file is binary.
    
    Args:
        file_path: Path to the file to check
        
    Returns:
        True if the file is binary, False otherwise
    """
    mime_type = magic.from_file(str(file_path), mime=True)
    return mime_type.startswith('application/')

def get_file_info(file_path: Path) -> Tuple[str, str, Optional[str]]:
    """Get file information including MIME type, extension, and language.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Tuple of (mime_type, extension, language)
    """
    mime_type = get_mime_type(file_path)
    extension = file_path.suffix.lower()
    
    # Get language using enhanced detection
    language, _ = detect_language(file_path)
    
    return mime_type, extension, language

def get_detailed_file_info(file_path: Path) -> dict:
    """Get detailed file information including language detection stats.
    
    Args:
        file_path: Path to the file
        
    Returns:
        Dictionary containing detailed file information
    """
    # Get basic file info
    mime_type = get_mime_type(file_path)
    extension = file_path.suffix.lower()
    is_binary = is_binary_file(file_path)
    
    # Get language detection stats
    lang_stats = get_language_stats(file_path)
    
    # Combine all information
    return {
        'path': str(file_path),
        'mime_type': mime_type,
        'extension': extension,
        'is_binary': is_binary,
        'language': lang_stats['language'],
        'detection_method': lang_stats['detection_method'],
        'confidence': lang_stats.get('confidence', {}),
        'size': file_path.stat().st_size,
        'modified': file_path.stat().st_mtime,
    } 