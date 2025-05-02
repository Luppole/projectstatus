#!/usr/bin/env python3

# Language mappings
EXT_LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript', '.jsx': 'JSX',
    '.tsx': 'TSX', '.java': 'Java', '.c': 'C', '.cpp': 'C++', '.cs': 'C#',
    '.go': 'Go', '.rs': 'Rust', '.swift': 'Swift', '.kt': 'Kotlin', '.m': 'Objective-C',
    '.rb': 'Ruby', '.php': 'PHP', '.html': 'HTML', '.css': 'CSS',
    '.scss': 'Sass', '.vue': 'Vue', '.sh': 'Shell', '.lua': 'Lua'
}

# Comment syntax for different languages
COMMENT_SYNTAX = {
    'Python': '#', 'JavaScript': '//', 'TypeScript': '//', 'C++': '//', 'C': '//', 'Java': '//',
    'C#': '//', 'Go': '//', 'Rust': '//', 'Swift': '//', 'Kotlin': '//', 'Objective-C': '//',
    'Ruby': '#', 'PHP': '//', 'Shell': '#', 'Lua': '--'
}

# UI Themes
THEMES = {
    "light": {"info": "black on white", "warning": "yellow"},
    "dark":  {"info": "white on black", "warning": "bright_yellow"},
    "neon":  {"info": "magenta", "warning": "cyan"},
    "matrix":{"info": "green", "warning": "bright_green"},
}

# Security scan patterns
SECURITY_PATTERNS = {
    'environment_file': [r'\.env$', r'\.env\.[a-zA-Z0-9]+$'],
    'secret_file': [r'secret[s]?\.', r'credential[s]?\.', r'password[s]?\.'],
    'private_key': [r'id_rsa$', r'\.pem$', r'\.key$', r'\.pfx$'],
    'config_file': [r'config\.', r'settings\.']
}

# Test patterns for coverage estimation
TEST_PATTERNS = [
    r'test[s]?/', r'test[s]?\.', r'_test\.', 
    r'spec[s]?/', r'spec[s]?\.', r'_spec\.'
]

# Constants
LARGE_SCRIPT_THRESHOLD = 1000  # Lines of code 