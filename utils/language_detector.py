#!/usr/bin/env python3
import re
import os
from pathlib import Path
from typing import Tuple, Optional, Dict, List
import magic

# Common shebang patterns and their corresponding languages
SHEBANG_PATTERNS = {
    r'^#!.*\bpython[23]?\b': 'Python',
    r'^#!.*\bperl\b': 'Perl',
    r'^#!.*\bruby\b': 'Ruby',
    r'^#!.*\bbash\b': 'Shell',
    r'^#!.*\bsh\b': 'Shell',
    r'^#!.*\bnode\b': 'JavaScript',
    r'^#!.*\bphp\b': 'PHP',
}

# Common language markers in file content
LANGUAGE_MARKERS = {
    'Python': [
        r'^import\s+\w+',
        r'^from\s+\w+\s+import',
        r'^def\s+\w+\s*\(',
        r'^class\s+\w+',
    ],
    'JavaScript': [
        r'^import\s+.*from',
        r'^const\s+\w+\s*=',
        r'^let\s+\w+\s*=',
        r'^function\s+\w+\s*\(',
    ],
    'Ruby': [
        r'^require\s+[\'"]',
        r'^def\s+\w+\s*',
        r'^class\s+\w+',
    ],
    'PHP': [
        r'^<\?php',
        r'^namespace\s+\w+',
        r'^class\s+\w+',
    ],
    'Shell': [
        r'^if\s+\[',
        r'^for\s+\w+\s+in',
        r'^while\s+\[',
    ],
}

# File extension to language mapping
EXTENSION_MAP = {
    '.py': 'Python',
    '.js': 'JavaScript',
    '.jsx': 'JavaScript',
    '.ts': 'TypeScript',
    '.tsx': 'TypeScript',
    '.rb': 'Ruby',
    '.php': 'PHP',
    '.pl': 'Perl',
    '.sh': 'Shell',
    '.bash': 'Shell',
    '.zsh': 'Shell',
    '.java': 'Java',
    '.cpp': 'C++',
    '.c': 'C',
    '.h': 'C',
    '.hpp': 'C++',
    '.cs': 'C#',
    '.go': 'Go',
    '.rs': 'Rust',
    '.swift': 'Swift',
    '.kt': 'Kotlin',
    '.scala': 'Scala',
    '.m': 'Objective-C',
    '.mm': 'Objective-C++',
    '.r': 'R',
    '.jl': 'Julia',
    '.hs': 'Haskell',
    '.fs': 'F#',
    '.clj': 'Clojure',
    '.lua': 'Lua',
    '.sql': 'SQL',
    '.html': 'HTML',
    '.css': 'CSS',
    '.scss': 'SCSS',
    '.sass': 'Sass',
    '.less': 'Less',
    '.xml': 'XML',
    '.json': 'JSON',
    '.yaml': 'YAML',
    '.yml': 'YAML',
    '.toml': 'TOML',
    '.ini': 'INI',
    '.md': 'Markdown',
    '.rst': 'reStructuredText',
    '.tex': 'TeX',
    '.txt': 'Text',
}

def detect_shebang(content: str) -> Optional[str]:
    """Detect language from shebang line."""
    first_line = content.split('\n')[0].strip()
    for pattern, language in SHEBANG_PATTERNS.items():
        if re.match(pattern, first_line, re.IGNORECASE):
            return language
    return None

def detect_from_content(content: str) -> Optional[str]:
    """Detect language from file content using markers."""
    # Count matches for each language
    matches: Dict[str, int] = {}
    
    for language, patterns in LANGUAGE_MARKERS.items():
        matches[language] = sum(
            1 for pattern in patterns
            if re.search(pattern, content, re.MULTILINE)
        )
    
    # Return language with most matches
    if matches:
        return max(matches.items(), key=lambda x: x[1])[0]
    return None

def detect_from_extension(file_path: Path) -> Optional[str]:
    """Detect language from file extension."""
    return EXTENSION_MAP.get(file_path.suffix.lower())

def detect_language(file_path: Path) -> Tuple[Optional[str], str]:
    """Detect programming language using multiple heuristics.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Tuple of (detected_language, detection_method)
    """
    # First try extension
    ext_lang = detect_from_extension(file_path)
    if ext_lang:
        return ext_lang, 'extension'
    
    # Skip binary files
    if magic.from_file(str(file_path), mime=True).startswith('application/'):
        return None, 'binary'
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Try shebang
        shebang_lang = detect_shebang(content)
        if shebang_lang:
            return shebang_lang, 'shebang'
        
        # Try content analysis
        content_lang = detect_from_content(content)
        if content_lang:
            return content_lang, 'content'
            
    except Exception:
        pass
    
    return None, 'unknown'

def get_language_stats(file_path: Path) -> Dict[str, any]:
    """Get detailed language detection statistics for a file.
    
    Args:
        file_path: Path to the file to analyze
        
    Returns:
        Dictionary containing language detection results and metadata
    """
    language, method = detect_language(file_path)
    
    stats = {
        'language': language,
        'detection_method': method,
        'extension': file_path.suffix.lower(),
        'mime_type': magic.from_file(str(file_path), mime=True),
    }
    
    if language:
        stats['confidence'] = {
            'extension': 1.0 if method == 'extension' else 0.0,
            'shebang': 1.0 if method == 'shebang' else 0.0,
            'content': 1.0 if method == 'content' else 0.0,
        }
    
    return stats 