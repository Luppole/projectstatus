import os
import pytest
from pathlib import Path

@pytest.fixture
def test_dir(tmp_path):
    """Create a temporary directory with test files."""
    # Create test files with different languages
    files = {
        'test.py': 'print("Hello")\n# Comment\n\n',
        'test.js': 'console.log("Hello");\n// Comment\n\n',
        'test.java': 'public class Test {\n    // Comment\n    public static void main() {}\n}\n',
        'test.cpp': '#include <iostream>\n// Comment\nint main() {}\n',
        'test.txt': 'This is a text file\n',
        'test.bin': b'\x00\x01\x02\x03',  # Binary file
        'test.sh': '#!/bin/bash\necho "Hello"\n# Comment\n\n',
        'test.md': '# Markdown\n\nSome text\n',
        'test.json': '{"key": "value"}\n',
        'test.xml': '<?xml version="1.0"?>\n<root></root>\n',
    }
    
    for filename, content in files.items():
        file_path = tmp_path / filename
        if isinstance(content, bytes):
            file_path.write_bytes(content)
        else:
            file_path.write_text(content)
    
    return tmp_path

@pytest.fixture
def large_test_dir(tmp_path):
    """Create a temporary directory with many files for performance testing."""
    # Create 1000 Python files with random content
    for i in range(1000):
        file_path = tmp_path / f'test_{i}.py'
        content = f'def test_{i}():\n    print("Test {i}")\n'
        file_path.write_text(content)
    
    return tmp_path 