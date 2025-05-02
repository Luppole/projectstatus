import pytest
from pathlib import Path
from utils.language_detector import (
    detect_language,
    detect_shebang,
    detect_from_content,
    detect_from_extension,
    get_language_stats
)

def test_detect_from_extension(test_dir):
    """Test language detection from file extensions."""
    # Test Python file
    assert detect_from_extension(test_dir / 'test.py') == 'Python'
    
    # Test JavaScript file
    assert detect_from_extension(test_dir / 'test.js') == 'JavaScript'
    
    # Test unknown extension
    assert detect_from_extension(test_dir / 'test.xyz') is None

def test_detect_shebang(test_dir):
    """Test shebang detection."""
    # Create a Python script with shebang
    python_script = test_dir / 'script'
    python_script.write_text('#!/usr/bin/env python3\nprint("Hello")')
    assert detect_shebang(python_script.read_text()) == 'Python'
    
    # Create a shell script with shebang
    shell_script = test_dir / 'script.sh'
    shell_script.write_text('#!/bin/bash\necho "Hello"')
    assert detect_shebang(shell_script.read_text()) == 'Shell'
    
    # Test file without shebang
    no_shebang = test_dir / 'no_shebang'
    no_shebang.write_text('print("Hello")')
    assert detect_shebang(no_shebang.read_text()) is None

def test_detect_from_content(test_dir):
    """Test language detection from content."""
    # Create Python file
    python_file = test_dir / 'python_file'
    python_file.write_text('import os\ndef hello():\n    pass')
    assert detect_from_content(python_file.read_text()) == 'Python'
    
    # Create JavaScript file
    js_file = test_dir / 'js_file'
    js_file.write_text('const x = 1;\nfunction hello() {}')
    assert detect_from_content(js_file.read_text()) == 'JavaScript'
    
    # Test file with no clear markers
    no_markers = test_dir / 'no_markers'
    no_markers.write_text('Hello World')
    assert detect_from_content(no_markers.read_text()) is None

def test_detect_language(test_dir):
    """Test complete language detection."""
    # Test Python file with extension
    py_file = test_dir / 'test.py'
    py_file.write_text('print("Hello")')
    lang, method = detect_language(py_file)
    assert lang == 'Python'
    assert method == 'extension'
    
    # Test extensionless Python file with shebang
    py_script = test_dir / 'script'
    py_script.write_text('#!/usr/bin/env python3\nprint("Hello")')
    lang, method = detect_language(py_script)
    assert lang == 'Python'
    assert method == 'shebang'
    
    # Test extensionless Python file with content
    py_content = test_dir / 'content'
    py_content.write_text('import os\ndef hello():\n    pass')
    lang, method = detect_language(py_content)
    assert lang == 'Python'
    assert method == 'content'
    
    # Test binary file
    bin_file = test_dir / 'test.bin'
    bin_file.write_bytes(b'\x00\x01\x02\x03')
    lang, method = detect_language(bin_file)
    assert lang is None
    assert method == 'binary'

def test_get_language_stats(test_dir):
    """Test getting detailed language statistics."""
    # Test Python file
    py_file = test_dir / 'test.py'
    py_file.write_text('print("Hello")')
    stats = get_language_stats(py_file)
    
    assert stats['language'] == 'Python'
    assert stats['detection_method'] == 'extension'
    assert stats['extension'] == '.py'
    assert stats['confidence']['extension'] == 1.0
    assert stats['confidence']['shebang'] == 0.0
    assert stats['confidence']['content'] == 0.0
    
    # Test extensionless Python file with shebang
    py_script = test_dir / 'script'
    py_script.write_text('#!/usr/bin/env python3\nprint("Hello")')
    stats = get_language_stats(py_script)
    
    assert stats['language'] == 'Python'
    assert stats['detection_method'] == 'shebang'
    assert stats['extension'] == ''
    assert stats['confidence']['extension'] == 0.0
    assert stats['confidence']['shebang'] == 1.0
    assert stats['confidence']['content'] == 0.0

def test_edge_cases(test_dir):
    """Test edge cases in language detection."""
    # Test empty file
    empty_file = test_dir / 'empty'
    empty_file.write_text('')
    lang, method = detect_language(empty_file)
    assert lang is None
    assert method == 'unknown'
    
    # Test very large file
    large_file = test_dir / 'large'
    large_file.write_text('print("Hello")\n' * 10000)
    lang, method = detect_language(large_file)
    assert lang == 'Python'
    assert method == 'content'
    
    # Test file with mixed content
    mixed_file = test_dir / 'mixed'
    mixed_file.write_text('#!/usr/bin/env python3\nconst x = 1;')
    lang, method = detect_language(mixed_file)
    assert lang == 'Python'  # Shebang takes precedence
    assert method == 'shebang' 